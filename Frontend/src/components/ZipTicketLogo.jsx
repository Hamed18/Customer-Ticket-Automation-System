import React from 'react'

export const ZipTicketLogo = ({ size = 'md', showBadge = true }) => {
  const isLg = size === 'lg'
  const iconSize = isLg ? 40 : 26

  return (
    <div className={`zipticket-logo ${isLg ? 'zipticket-logo-lg' : ''}`}>
      <div className={`zipticket-icon-wrap ${isLg ? 'zipticket-icon-wrap-lg' : ''}`}>
        <svg
          width={iconSize}
          height={iconSize}
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Rounded ticket backdrop */}
          <rect
            x="2"
            y="4"
            width="28"
            height="24"
            rx="6"
            fill="url(#ztBgGrad)"
            stroke="url(#ztStrokeGrad)"
            strokeWidth="1.5"
          />
          {/* Left/right ticket notches */}
          <circle cx="2" cy="16" r="3" fill="#0f172a" />
          <circle cx="30" cy="16" r="3" fill="#0f172a" />
          {/* Electric fast lightning bolt inside */}
          <path
            d="M17.5 7L10.5 16H16L14.5 25L22.5 14.5H16.5L17.5 7Z"
            fill="url(#ztBoltGrad)"
            stroke="#ffffff"
            strokeWidth="0.8"
            strokeLinejoin="round"
          />
          <defs>
            <linearGradient id="ztBgGrad" x1="2" y1="4" x2="30" y2="28" gradientUnits="userSpaceOnUse">
              <stop stopColor="#1e1b4b" />
              <stop offset="1" stopColor="#0f172a" />
            </linearGradient>
            <linearGradient id="ztStrokeGrad" x1="2" y1="4" x2="30" y2="28" gradientUnits="userSpaceOnUse">
              <stop stopColor="#6366f1" />
              <stop offset="1" stopColor="#38bdf8" />
            </linearGradient>
            <linearGradient id="ztBoltGrad" x1="10.5" y1="7" x2="22.5" y2="25" gradientUnits="userSpaceOnUse">
              <stop stopColor="#38bdf8" />
              <stop offset="1" stopColor="#a855f7" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      <div className="zipticket-text-wrap">
        <span className="zipticket-text">
          <span className="zipticket-zip">Zip</span>
          <span className="zipticket-ticket">Ticket</span>
        </span>
        {showBadge && (
          <span className="zipticket-badge">AI</span>
        )}
      </div>
    </div>
  )
}
export default ZipTicketLogo
