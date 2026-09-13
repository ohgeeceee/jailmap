export interface State {
  id: string
  name: string
  abbrev: string
  fipsCode: string
  _count?: {
    counties: number
    jails: number
  }
}

export interface County {
  id: string
  name: string
  fipsCode: string
  stateId: string
  _count?: {
    jails: number
  }
}

export interface Jail {
  id: string
  name: string
  address?: string | null
  city?: string | null
  zipCode?: string | null
  phone?: string | null
  website?: string | null
  latitude?: number | null
  longitude?: number | null
  countyId: string
  stateId: string
  isActive: boolean
  county?: County
  state?: State
  _count?: {
    rosters: number
  }
}

export interface Roster {
  id: string
  jailId: string
  inmateName: string
  bookingNumber?: string | null
  bookingDate?: Date | string | null
  releaseDate?: Date | string | null
  charges: string[]
  bondAmount?: number | null
  mugshotUrl?: string | null
  age?: number | null
  gender?: string | null
  race?: string | null
  scrapeDate: Date | string
}

export interface ApiResponse<T> {
  data: T | null
  error?: string
  meta?: {
    total?: number
    page?: number
    limit?: number
  }
}

export interface SearchParams {
  query?: string
  page?: number
  limit?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}