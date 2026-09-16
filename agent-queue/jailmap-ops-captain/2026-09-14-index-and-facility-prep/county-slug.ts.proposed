// Shared county slug + key normalizer.
//
// Why this exists: the two sides of JailMap disagree on county naming.
//   public."County".name         = "Flathead County"
//   records.jurisdictions.county = "Flathead"
// Any join or slug built without stripping the trailing " County" fails silently,
// which is exactly how a county page ends up 404-ing while its data is present.
//
// Existing URLs (/county/MT/flathead) remain valid — stripping the suffix is a
// no-op for names that never had it.

export function countyKey(name: string): string {
  return name
    .toLowerCase()
    .replace(/\s+county$/, '')
    .trim()
}

export function slugifyCounty(name: string): string {
  return countyKey(name)
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
}
