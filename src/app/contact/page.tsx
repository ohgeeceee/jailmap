import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { Mail, MapPin, MessageSquare, Phone } from 'lucide-react'
import { ContactForm } from '@/components/support/ContactForm'

export const metadata = {
  title: 'Contact Us',
  description: 'Get in touch with the JailMap team — support, partnerships, press, and general inquiries.',
  alternates: { canonical: '/contact' },
  openGraph: {
    title: 'Contact Us | JailMap',
    description: 'Get in touch with the JailMap team — support, partnerships, press, and general inquiries.',
    url: 'https://jailmap.com/contact',
    siteName: 'JailMap',
  },
}

export default function ContactPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <section className="mx-auto w-full max-w-4xl px-5 py-16">
          <h1 className="text-4xl font-bold">Contact us</h1>
          <p className="mt-3 text-lg text-[var(--muted)]">
            Have a question, partnership idea, or press inquiry? Reach out directly.
          </p>
        </section>

        <section className="mx-auto w-full max-w-5xl px-5 pb-20">
          <div className="rounded-lg bg-white border border-[var(--line)] p-8 mb-8"><h2 className="text-2xl font-semibold">Send us a message</h2><p className="mt-2 mb-6 text-[var(--muted)]">Your message becomes a private support ticket for the JailMap team.</p><ContactForm /></div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <article className="rounded-lg border border-[var(--line)] bg-white p-6 flex flex-col">
              <MessageSquare size={28} className="text-[var(--green)]" />
              <h2 className="mt-4 text-xl font-semibold">General support</h2>
              <p className="mt-2 text-[var(--muted)]">Account help, bug reports, feature requests — we read every message.</p>
              <div className="mt-6 pt-6 border-t border-[var(--line)]">
                <Mail size={16} className="inline text-[var(--muted)]" />
                <a href="mailto:getjailmap@gmail.com" className="ml-2 text-[var(--green)] hover:underline">getjailmap@gmail.com</a>
              </div>
            </article>

            <article className="rounded-lg border border-[var(--line)] bg-white p-6 flex flex-col">
              <Phone size={28} className="text-[var(--green)]" />
              <h2 className="mt-4 text-xl font-semibold">Press & media</h2>
              <p className="mt-2 text-[var(--muted)]">Interview requests, data inquiries, and media partnerships.</p>
              <div className="mt-6 pt-6 border-t border-[var(--line)]">
                <Mail size={16} className="inline text-[var(--muted)]" />
                <a href="mailto:getjailmap@gmail.com?subject=Press%20and%20Media%20Inquiry" className="ml-2 text-[var(--green)] hover:underline">getjailmap@gmail.com</a>
              </div>
            </article>

            <article className="rounded-lg border border-[var(--line)] bg-white p-6 flex flex-col">
              <MapPin size={28} className="text-[var(--green)]" />
              <h2 className="mt-4 text-xl font-semibold">Partnerships</h2>
              <p className="mt-2 text-[var(--muted)]">Researchers, journalists, and organizations interested in data access.</p>
              <div className="mt-6 pt-6 border-t border-[var(--line)]">
                <Mail size={16} className="inline text-[var(--muted)]" />
                <a href="mailto:getjailmap@gmail.com?subject=Partnership%20Inquiry" className="ml-2 text-[var(--green)] hover:underline">getjailmap@gmail.com</a>
              </div>
            </article>
          </div>
        </section>

        <section className="mx-auto w-full max-w-4xl px-5 pb-20">
          <div className="rounded-lg bg-white border border-[var(--line)] p-8">
            <h2 className="text-2xl font-semibold">Mailing address</h2>
            <p className="mt-3 text-[var(--muted)]">
              JailMap<br />
              Great Falls, Montana<br />
              United States
            </p>
            <p className="mt-6 text-sm text-[var(--muted)]">
              Response time is typically 1–2 business days. For account-specific issues, include the email address associated with your account.
            </p>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
