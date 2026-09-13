import Link from 'next/link'
import { MapPin } from 'lucide-react'
export function Brand({ light = false }: { light?: boolean }) {
  return <Link href="/" className={`brand ${light ? 'brand-light' : ''}`} aria-label="JailMap home"><span className="brand-mark"><MapPin size={21} strokeWidth={2.4} /></span><span>jailmap<span className="brand-dot">.</span></span></Link>
}
