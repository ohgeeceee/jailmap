'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Search, Building2, MapPin, ChevronRight, Filter } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { State, County } from '@/types'
import { cn } from '@/lib/utils'

interface StatePageClientProps {
  state: State & { counties: (County & { _count: { jails: number } })[] }
  counties: (County & { _count: { jails: number } })[]
  totalJails: number
}

export function StatePageClient({ state, counties, totalJails }: StatePageClientProps) {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCounty, setSelectedCounty] = useState<string | null>(null)

  const filteredCounties = counties.filter((county) =>
    county.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleCountyClick = (countyId: string) => {
    setSelectedCounty(selectedCounty === countyId ? null : countyId)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <MapPin className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900 dark:text-white">JailMap</span>
            </Link>
            <nav className="flex items-center gap-4">
              <Link href="/pricing" className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-blue-600">Pricing</Link>
              <Link href="/api-docs" className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-blue-600">API</Link>
              <Link className="rounded px-3 py-2 text-sm hover:bg-gray-100" href="/login">Sign In</Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <Link href="/" className="inline-flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 mb-4">
            <ChevronRight className="h-4 w-4 rotate-180" />
            Back to Map
          </Link>
          <div className="flex items-center gap-4">
            <MapPin className="h-10 w-10 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{state.name}</h1>
              <p className="text-gray-600 dark:text-gray-300">
                {state._count?.counties || counties.length} counties • {totalJails} facilities
              </p>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-4">
                <Filter className="h-5 w-5 text-gray-500" />
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Search Counties</h2>
              </div>
              <Input
                placeholder="Search counties..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="max-w-md"
              />
            </div>

            {filteredCounties.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">No counties found matching your search.</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {filteredCounties.map((county) => (
                  <Card
                    key={county.id}
                    className={cn(
                      'transition-all duration-200',
                      selectedCounty === county.id && 'ring-2 ring-blue-500 border-blue-500'
                    )}
                    onClick={() => handleCountyClick(county.id)}
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <Building2 className="h-6 w-6 text-blue-600 flex-shrink-0" />
                          <div>
                            <h3 className="font-semibold text-gray-900 dark:text-white">{county.name} County</h3>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              {county._count.jails} facilit{county._count.jails === 1 ? 'y' : 'ies'}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <Badge variant="outline">{county._count.jails} Jails</Badge>
                          <ChevronRight className="h-5 w-5 text-gray-400" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {filteredCounties.length > 0 && (
              <div className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
                Showing {filteredCounties.length} of {counties.length} counties
              </div>
            )}
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="h-5 w-5" />
                  State Info
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Total Counties</span>
                  <span className="font-medium">{counties.length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Total Facilities</span>
                  <span className="font-medium">{totalJails}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">State Abbreviation</span>
                  <span className="font-medium">{state.abbrev}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">FIPS Code</span>
                  <span className="font-medium font-mono">{state.fipsCode}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="h-5 w-5" />
                  Quick Search
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input
                  placeholder="Search inmates statewide..."
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.currentTarget.value) {
                      router.push(`/search?state=${state.abbrev}&name=${encodeURIComponent(e.currentTarget.value)}`)
                    }
                  }}
                />
                  <Link className="block w-full rounded border px-4 py-2 text-center" href={`/search?state=${state.abbrev}`}>
                    Advanced Search
                  </Link>
              </CardContent>
            </Card>

            <Card className="border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-900/20">
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-blue-800 dark:text-blue-200 mb-3">
                    Need programmatic access?
                  </p>
                    <Link href="/dashboard" className="block rounded bg-blue-600 px-4 py-2 text-white">Open your workspace</Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>&copy; {new Date().getFullYear()} JailMap. Data from public records.</p>
        </div>
      </footer>
    </div>
  )
}
