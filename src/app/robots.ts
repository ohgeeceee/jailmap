import type { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/api/', '/admin', '/login', '/register', '/dashboard', '/inmate/'],
      },
    ],
    sitemap: 'https://jailmap.com/sitemap.xml',
  }
}
