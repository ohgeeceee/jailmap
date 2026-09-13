'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { US_STATES } from '@/lib/states'

const statePaths: Record<string, string> = {
  AL: "M331,297 L331,321 L307,321 L307,297 Z",
  AK: "M50,260 L80,260 L80,290 L50,290 Z",
  AZ: "M107,247 L147,247 L147,287 L107,287 Z",
  AR: "M251,257 L281,257 L281,297 L251,297 Z",
  CA: "M17,187 L67,187 L67,247 L17,247 Z",
  CO: "M167,177 L207,177 L207,217 L167,217 Z",
  CT: "M437,107 L457,107 L457,117 L437,117 Z",
  DE: "M417,137 L427,137 L427,147 L417,147 Z",
  FL: "M341,337 L371,337 L371,387 L341,387 Z",
  GA: "M331,287 L361,287 L361,337 L331,337 Z",
  HI: "M30,350 L50,350 L50,370 L30,370 Z",
  ID: "M77,117 L107,117 L107,157 L77,157 Z",
  IL: "M297,167 L337,167 L337,217 L297,217 Z",
  IN: "M337,137 L367,137 L367,167 L337,167 Z",
  IA: "M257,127 L297,127 L297,167 L257,167 Z",
  KS: "M217,177 L257,177 L257,217 L217,217 Z",
  KY: "M337,197 L367,197 L367,237 L337,237 Z",
  LA: "M281,297 L311,297 L311,337 L281,337 Z",
  ME: "M447,57 L477,57 L477,97 L447,97 Z",
  MD: "M407,137 L427,137 L427,157 L407,157 Z",
  MA: "M447,87 L467,87 L467,107 L447,107 Z",
  MI: "M367,77 L407,77 L407,137 L367,137 Z",
  MN: "M257,67 L307,67 L307,127 L257,127 Z",
  MS: "M301,277 L331,277 L331,317 L301,317 Z",
  MO: "M257,197 L297,197 L297,237 L257,237 Z",
  MT: "M117,47 L157,47 L157,87 L117,87 Z",
  NE: "M207,127 L247,127 L247,167 L207,167 Z",
  NV: "M77,157 L117,157 L117,207 L77,207 Z",
  NH: "M447,67 L467,67 L467,87 L447,87 Z",
  NJ: "M427,117 L447,117 L447,137 L427,137 Z",
  NM: "M147,217 L187,217 L187,257 L147,257 Z",
  NY: "M407,87 L447,87 L447,127 L407,127 Z",
  NC: "M361,227 L391,227 L391,277 L361,277 Z",
  ND: "M207,57 L247,57 L247,97 L207,97 Z",
  OH: "M367,157 L397,157 L397,187 L367,187 Z",
  OK: "M221,217 L261,217 L261,257 L221,257 Z",
  OR: "M37,117 L77,117 L77,157 L37,157 Z",
  PA: "M397,117 L427,117 L427,147 L397,147 Z",
  RI: "M457,107 L467,107 L467,117 L457,117 Z",
  SC: "M361,277 L381,277 L381,317 L361,317 Z",
  SD: "M207,87 L247,87 L247,127 L207,127 Z",
  TN: "M321,237 L351,237 L351,277 L321,277 Z",
  TX: "M221,257 L291,257 L291,337 L221,337 Z",
  UT: "M137,177 L177,177 L177,217 L137,217 Z",
  VT: "M437,67 L457,67 L457,87 L437,87 Z",
  VA: "M381,167 L411,167 L411,217 L381,217 Z",
  WA: "M27,67 L67,67 L67,117 L27,117 Z",
  WV: "M377,147 L407,147 L407,177 L377,177 Z",
  WI: "M307,87 L347,87 L347,127 L307,127 Z",
  WY: "M157,97 L197,97 L197,137 L157,137 Z",
  DC: "M407,147 L417,147 L417,157 L407,157 Z",
}

const stateCentroids: Record<string, [number, number]> = {
  AL: [319, 309], AK: [65, 275], AZ: [127, 267], AR: [266, 277],
  CA: [42, 217], CO: [187, 197], CT: [447, 112], DE: [422, 142],
  FL: [356, 362], GA: [346, 312], HI: [40, 360], ID: [92, 137],
  IL: [317, 192], IN: [352, 152], IA: [277, 147], KS: [237, 197],
  KY: [352, 217], LA: [296, 317], ME: [462, 77], MD: [417, 147],
  MA: [457, 97], MI: [387, 107], MN: [282, 97], MS: [316, 297],
  MO: [277, 217], MT: [137, 67], NE: [227, 147], NV: [97, 182],
  NH: [457, 77], NJ: [437, 127], NM: [167, 237], NY: [427, 107],
  NC: [376, 252], ND: [227, 77], OH: [382, 172], OK: [241, 237],
  OR: [57, 137], PA: [412, 132], RI: [462, 112], SC: [371, 297],
  SD: [227, 107], TN: [336, 257], TX: [256, 297], UT: [157, 197],
  VT: [447, 77], VA: [396, 192], WA: [47, 92], WV: [392, 162],
  WI: [327, 107], WY: [177, 117], DC: [412, 152],
}

interface USMapProps {
  onStateClick?: (abbrev: string) => void
  selectedState?: string
  className?: string
}

export function USMap({ onStateClick, selectedState, className }: USMapProps) {
  const [hoveredState, setHoveredState] = useState<string | null>(null)

  const handleClick = (abbrev: string) => {
    onStateClick?.(abbrev)
  }

  return (
    <div className={cn('relative w-full max-w-4xl mx-auto', className)}>
      <svg
        viewBox="0 0 500 400"
        preserveAspectRatio="xMidYMid meet"
        className="w-full h-auto cursor-pointer"
        role="img"
        aria-label="Interactive map of United States"
      >
        <defs>
          <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="2" floodColor="#000" floodOpacity="0.1" />
          </filter>
        </defs>
        
        {US_STATES.map((state) => {
          const path = statePaths[state.abbrev]
          const [cx, cy] = stateCentroids[state.abbrev] || [0, 0]
          const isSelected = selectedState === state.abbrev
          const isHovered = hoveredState === state.abbrev
          
          if (!path) return null

          return (
            <g key={state.abbrev}>
              <path
                d={path}
                fill={isSelected 
                  ? '#2563eb' 
                  : isHovered 
                  ? '#3b82f6' 
                  : '#e5e7eb'}
                stroke={isSelected ? '#1d4ed8' : '#9ca3af'}
                strokeWidth={isSelected ? 2 : 1}
                filter="url(#shadow)"
                onMouseEnter={() => setHoveredState(state.abbrev)}
                onMouseLeave={() => setHoveredState(null)}
                onClick={() => handleClick(state.abbrev)}
                style={{ cursor: 'pointer', transition: 'all 0.2s ease' }}
                data-state={state.abbrev}
                aria-label={state.name}
              />
              <text
                x={cx}
                y={cy}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="7"
                fontWeight={isSelected ? 'bold' : 'normal'}
                fill={isSelected ? 'white' : '#374151'}
                pointerEvents="none"
                className="select-none"
              >
                {state.abbrev}
              </text>
            </g>
          )
        })}
      </svg>
      
      <div className="mt-4 flex flex-wrap justify-center gap-1 text-xs text-gray-500">
        {US_STATES.map((state) => (
          <span
            key={state.abbrev}
            className={cn(
              'px-2 py-1 rounded transition-colors cursor-pointer',
              selectedState === state.abbrev 
                ? 'bg-blue-100 text-blue-700 font-medium' 
                : 'hover:bg-gray-100'
            )}
            onClick={() => handleClick(state.abbrev)}
          >
            {state.abbrev}
          </span>
        ))}
      </div>
    </div>
  )
}
