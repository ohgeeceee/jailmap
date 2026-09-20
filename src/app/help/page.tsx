import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { ArrowRight, CheckCircle2, ChevronRight, HelpCircle, Mail, Search } from 'lucide-react'

export const metadata = {
  title: 'Help & FAQ',
  description: 'Frequently asked questions about JailMap — search, accounts, privacy reviews, and how the service works.',
  alternates: { canonical: 'https://jailmap.com/help' },
  openGraph: {
    title: 'Help & FAQ | JailMap',
    description: 'Frequently asked questions about JailMap — search, accounts, privacy reviews, and how the service works.',
    url: 'https://jailmap.com/help',
  },
}

const faqs = [
  {
    question: 'What is JailMap?',
    answer: 'JailMap is a public-records platform that aggregates official booking records from sheriff\'s offices, detention facilities, and their authorized vendors across the United States. Every record links directly to the original source.',
  },
  {
    question: 'Is JailMap a government website?',
    answer: 'No. JailMap is an independent, privately operated service. We are not affiliated with any government agency. We publish only records that are already public, with attribution.',
  },
  {
    question: 'Is search really free?',
    answer: 'Yes. Searching public booking records and submitting correction or removal requests costs nothing. There is no paywall on the public site.',
  },
  {
    question: 'How do I create an account?',
    answer: 'Click "Create account" in the top navigation. Account creation is free and lets you save searches and manage your requests.',
  },
  {
    question: 'Can I request removal of a record?',
    answer: 'Yes. You can submit a free correction or removal request directly from any record page. JailMap reviews every request, though removal is not guaranteed. A paid privacy review ($99) provides a human reviewer assessment for name redaction.',
  },
  {
    question: 'Does paying remove my record?',
    answer: 'No. The $99 fee covers a human privacy review of your name removal request. A reviewer decides whether to withhold your name from public pages based on the facts. Payment does not itself remove any record, and the underlying government record remains with its official source.',
  },
  {
    question: 'Where does the data come from?',
    answer: 'JailMap only aggregates records from authorized, official sources — county sheriff departments, detention facilities, and their official vendors. Every record links back to the original source.',
  },
  {
    question: 'How often are records updated?',
    answer: 'We ingest from each source on a regular schedule — typically every 2 to 6 hours for active jurisdictions. The exact frequency depends on the source.',
  },
  {
    question: 'How do I correct an error in a record?',
    answer: 'Use the "Request correction" link on any record page. Corrections are free. We verify changes before applying them.',
  },
  {
    question: 'How do I contact JailMap?',
    answer: 'Email us at getjailmap@gmail.com. We respond within 1–2 business days.',
  },
]

export default function HelpPage() {
  const faqJsonLd = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map((faq) => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: { '@type': 'Answer', text: faq.answer },
    })),
  }

  return (
    <div className="jm-theme">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <PublicHeader />
      <main id="main-content">
        <section className="mx-auto w-full max-w-4xl px-5 py-16">
          <h1 className="text-4xl font-bold">Help center</h1>
          <p className="mt-3 text-lg text-[var(--muted)]">
            Answers to common questions about JailMap.
          </p>
        </section>

        <section className="mx-auto w-full max-w-4xl px-5 pb-20">
          <div className="space-y-4">
            {faqs.map((faq) => (
              <article key={faq.question} className="rounded-lg border border-[var(--line)] bg-white p-6">
                <h2 className="text-lg font-semibold">{faq.question}</h2>
                <p className="mt-2 text-[var(--muted)]">{faq.answer}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mx-auto w-full max-w-4xl px-5 pb-20">
          <div className="rounded-lg bg-white border border-[var(--line)] p-8 text-center">
            <h2 className="text-2xl font-semibold">Still have questions?</h2>
            <p className="mt-3 text-[var(--muted)]">We're here to help. Reach out directly.</p>
            <a href="mailto:getjailmap@gmail.com?subject=JailMap%20Support" className="jm-button mt-6 inline-flex">Contact support <ArrowRight size={18} className="ml-2" /></a>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
