import { PrismaClient } from '@prisma/client'
import { PrismaPg } from '@prisma/adapter-pg'

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

function client() {
  if (!globalForPrisma.prisma) {
    if (!process.env.DATABASE_URL) throw new Error('Map database is not configured')
    globalForPrisma.prisma = new PrismaClient({ adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL }), log: ['error'] })
  }
  return globalForPrisma.prisma
}
// Lazy initialization allows builds and the account app to work without a map DB.
export const prisma = new Proxy({} as PrismaClient, { get(_target, property) {
  const instance = client()
  const value = Reflect.get(instance, property)
  return typeof value === 'function' ? value.bind(instance) : value
} })
