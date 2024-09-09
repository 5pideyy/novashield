import Koa, { Context, Next } from 'koa';
import Blacklist from './controllers/blacklist';
import config from './util/config-parser';
import Ratelimiter from './controllers/rate-limiter';
import Waf from './controllers/waf';
import NoSql from './util/nosql';
import { connectToDatabase } from './controllers/db';  // Correct relative import path
import mongoose from 'mongoose';

// Ensure MongoDB is connected
connectToDatabase().then(() => {
  console.log('MongoDB connection established in controller-service.ts');
}).catch((error) => {
  console.error('Error connecting to MongoDB in controller-service.ts:', error);
});

// Define schema for blocked requests and banned IPs
const blockedRequestSchema = new mongoose.Schema({
  ipAddress: String,
  blockedAt: { type: Date, default: Date.now },
  reason: String,
  requestUrl: String,
  userAgent: String,
});

// Create a model from the schema
const BlockedRequest = mongoose.model('BlockedRequest', blockedRequestSchema);

const nosql: NoSql = NoSql.getInstance();
const uuidTest = new RegExp(
  '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
);

export const controller = async (ctx: Context, next: Next) => {
  try {
    if (ctx.query.pow_token && uuidTest.test(ctx.query.pow_token as string)) {
      if (await nosql.get(`wht:${ctx.query.pow_token}`)) {
        await next();
        return;
      }
    }
    if (
      ctx.headers['PoW-Token'] &&
      uuidTest.test(ctx.headers['PoW-Token'] as string)
    ) {
      if (await nosql.get(`wht:${ctx.headers['PoW-Token']}`)) {
        await next();
        return;
      }
    }

    const blacklist = Blacklist.getInstance();
    const rateLimiter = Ratelimiter.getInstance();
    const waf = Waf.getInstance();
    await nosql.incr(`stats:ttl_req`);

    if (await blacklist.check(ctx.ip)) {
      const scanResult = await waf.scan(ctx);
      if (!scanResult) {
        if (!!ctx.session?.authorized || !config.pow) {
          if (config.rate_limit) {
            await Object.assign(
              ctx.session,
              await rateLimiter.process(ctx.ip, ctx.session)
            );
          }
          await next();
          return;
        } else {
          if (ctx.request.url === '/') {
            ctx.redirect('/pow');
            return;
          } else if (RegExp(`^/pow`).test(ctx.request.url)) {
            await next();
            return;
          } else {
            ctx.redirect(`/pow?redirect=${ctx.request.url as string}`);
            return;
          }
        }
      } else {
        // Log the blocked request due to WAF trigger
        console.log(
          `Rule ${scanResult.id}: "${scanResult.cmt}" in category "${
            scanResult.type
          }" has been triggered by request ${
            scanResult.location
          } at ${new Date().toISOString()}`
        );
        ctx.status = 403;
        await ctx.render('waf');

        // Save blocked request to MongoDB
        await logBlockedRequest(ctx, `WAF triggered: Rule ${scanResult.id}`);

        return;
      }
    }

    // If IP is blacklisted
    ctx.status = 403;
    await ctx.render('banned');

    // Save banned IP to MongoDB
    await logBlockedRequest(ctx, 'IP blacklisted');
  } catch (error) {
    console.error('Error in controller middleware:', error);
    ctx.status = 500;
    ctx.body = 'Internal Server Error';
  }
};

// Function to log blocked requests to MongoDB
const logBlockedRequest = async (ctx: Context, reason: string) => {
  const blockedRequest = new BlockedRequest({
    ipAddress: ctx.ip,
    reason: reason,
    requestUrl: ctx.request.url,
    userAgent: ctx.headers['user-agent'] || 'Unknown',
  });

  try {
    await blockedRequest.save();
    console.log(`Blocked request from IP ${ctx.ip} saved to MongoDB`);
  } catch (error) {
    console.error('Error saving blocked request to MongoDB:', error);
  }
};
