import { defineConfig } from 'prisma-legacy/config'
export default defineConfig({ schema: 'prisma/schema.prisma', datasource: { url: process.env.DATABASE_URL || 'postgresql://localhost:5432/jailmap' } })
