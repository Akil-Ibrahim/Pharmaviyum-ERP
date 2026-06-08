import { neon } from "@neondatabase/serverless";
import { drizzle } from "drizzle-orm/neon-http";

// Guard: during local frontend development DATABASE_URL may be missing.
// If it's not set, export a safe noop-like `db` object to avoid runtime crash.
let _db: any = null;
if (process.env.DATABASE_URL) {
	const sql = neon(process.env.DATABASE_URL);
	_db = drizzle({ client: sql });
} else {
	// Minimal fallback that throws a clear error when used.
	const thrower = () => {
		throw new Error(
			"DATABASE_URL is not set. Set DATABASE_URL in .env.local to enable DB access."
		);
	};
	_db = new Proxy(
		{},
		{
			get() {
				return thrower;
			},
			apply() {
				return thrower();
			},
		}
	);
}

export const db = _db;
