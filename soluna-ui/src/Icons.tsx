export const IconFile = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
    <path d="M13.71 4.29l-3-3L10 1H4L3 2v12l1 1h9l1-1V5l-.29-.71zM13 14H4V2h5v4h4v8z"/>
  </svg>
);

export const IconClose = () => (
  <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
    <path d="M7.116 8l-4.558 4.558.884.884L8 8.884l4.558 4.558.884-.884L8.884 8l4.558-4.558-.884-.884L8 7.116 3.442 2.558l-.884.884L7.116 8z"/>
  </svg>
);

export const IconChevronRight = ({ rotated }: { rotated?: boolean }) => (
  <svg 
    width="16" height="16" viewBox="0 0 16 16" fill="currentColor" 
    style={{ transform: rotated ? 'rotate(90deg)' : 'none', transition: 'transform 0.1s' }}
  >
    <path d="M6 4l4 4-4 4V4z"/>
  </svg>
);

export const IconError = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="#f87171">
    <path d="M8 1L1 14h14L8 1zm0 2.5L12.5 13H3.5L8 3.5zM7 11v1h2v-1H7zm0-5v4h2V6H7z"/>
  </svg>
);

export const IconCheck = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4ade80" strokeWidth="2">
    <path d="M20 6L9 17l-5-5"/>
  </svg>
);

export const IconPlay = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
    <path d="M4 2v12l10-6z"/>
  </svg>
);