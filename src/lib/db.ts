import { prisma } from './prisma'

export const pool = {
  async query(text: string) {
    const rows = await prisma.$queryRawUnsafe(text)
    return { rows: Array.isArray(rows) ? rows : [] }
  },
}
