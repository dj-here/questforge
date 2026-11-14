import { neon } from "@neondatabase/serverless";

export function getDbUrl(): string {
  const url =
    process.env.DATABASE_URL ||
    process.env.POSTGRES_URL ||
    process.env.POSTGRESQL_URL;

  if (!url) {
    throw new Error(
      "DATABASE_URL or POSTGRES_URL environment variable is missing. Please set it in Vercel project settings."
    );
  }
  return url;
}

export function getDb() {
  const url = getDbUrl();
  return neon(url);
}
