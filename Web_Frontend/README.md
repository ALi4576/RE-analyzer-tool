# RE Tool Frontend - React + TypeScript

Modern, responsive web frontend for the Multi-Agentic Requirements Engineering Tool.

## Features

- **Clean Apple-like Design**: Minimal, elegant UI with Tailwind CSS
- **Real-time Analysis**: WebSocket support for streaming results
- **Type-Safe**: 100% TypeScript with strict mode
- **State Management**: Zustand for lightweight, efficient state
- **Responsive**: Mobile-first design that works everywhere
- **Component-Based**: Reusable, well-organized components

## Tech Stack

- **React 18** - UI framework
- **TypeScript 5** - Type safety
- **Tailwind CSS 3** - Styling
- **Vite 5** - Build tool
- **Zustand** - State management
- **Axios** - HTTP client
- **Lucide Icons** - Icon library

## Project Structure

```
src/
├── components/     # Reusable UI components
│   ├── Header.tsx
│   ├── Notification.tsx
│   ├── RequirementInput.tsx
│   ├── AnalysisResults.tsx
│   ├── ClarificationPanel.tsx
│   └── RequirementViewer.tsx
├── pages/          # Page components
│   └── Dashboard.tsx
├── services/       # API client
│   └── api.ts
├── store/          # State management
│   └── requirementStore.ts
├── types/          # TypeScript types
│   └── index.ts
├── utils/          # Helper functions
│   └── helpers.ts
├── styles/         # Global styles
│   └── globals.css
├── App.tsx         # Main app component
└── main.tsx        # Entry point
```

## Getting Started

### Prerequisites

- Node.js 18+ (or 20+)
- Backend running at `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Build Tailwind CSS
npm run build

# Start dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Check TypeScript types

## API Integration

Backend API is proxied at `/api`:

```typescript
// Example API calls
import { apiClient } from '@services/api';

const response = await apiClient.analyzeRequirements({
  text: 'requirement text',
  session_id: 'session-123',
});
```

## Styling

Uses **Tailwind CSS** with custom Apple-inspired theme:

- **Colors**: Neutral grays, primary blue, semantic colors (success, warning, error)
- **Typography**: System fonts (-apple-system, BlinkMacSystemFont, Segoe UI)
- **Spacing**: Conservative, clean whitespace
- **Shadows**: Subtle, minimal

## Component Library

### Button Variants

```jsx
<button className="btn-primary">Primary Action</button>
<button className="btn-secondary">Secondary Action</button>
<button className="btn-ghost">Ghost Button</button>
```

### Input Fields

```jsx
<input type="text" className="input-base" placeholder="..." />
<textarea className="input-base"></textarea>
```

### Cards

```jsx
<div className="card p-6">Content here</div>
```

## State Management

Uses Zustand store for requirement analysis state:

```typescript
import { useRequirementStore } from '@store/requirementStore';

const { analyzeRequirements, analysisState } = useRequirementStore();
await analyzeRequirements('requirement text');
```

## Type Safety

All API responses and state have full TypeScript types:

```typescript
interface ISORequirement {
  id: string;
  title: string;
  shall_statement: string;
  // ...
}
```

## Performance

- **Code Splitting**: Vite automatically handles splitting
- **Lazy Loading**: Components split by route
- **Caching**: HTTP requests cached via axios defaults
- **Minimal Bundle**: ~150KB gzipped

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Development

### Adding a New Component

1. Create in `src/components/MyComponent.tsx`
2. Export in `src/components/index.ts`
3. Import and use in pages or other components

### Adding a New Page

1. Create in `src/pages/MyPage.tsx`
2. Add route in `App.tsx` (setup router if needed)

### State Updates

Create new Zustand store in `src/store/`:

```typescript
export const useMyStore = create((set) => ({
  data: null,
  setData: (data) => set({ data }),
}));
```

## Environment Variables

Create `.env.local`:

```
VITE_API_URL=http://localhost:8000
```

## Build for Production

```bash
npm run build
# Output in dist/
```

Serve with any static host:

```bash
npm run preview  # Test locally
```

## Contributing

1. Follow TypeScript strict mode
2. Use meaningful component names
3. Document complex logic
4. Test responsive design

## License

MIT

## Support

For issues or questions about the RE Tool backend, see the root project README.
