# Frontend Quick Start

Get the React frontend running in 2 minutes.

## 1. Install Dependencies

```bash
cd Web_Frontend
npm install
```

Expected output: ~500 packages installed in ~30 seconds

## 2. Start Dev Server

```bash
npm run dev
```

Expected output:
```
  VITE v5.0.0  ready in 456 ms

  ➜  Local:   http://localhost:3000/
  ➜  press h to show help
```

## 3. Open in Browser

Visit: [http://localhost:3000](http://localhost:3000)

You should see the RE Tool dashboard loaded and ready.

## Prerequisites

Make sure the backend is running:

```bash
# Terminal 1: Backend
cd ..
python main.py

# Terminal 2: Frontend
cd Web_Frontend
npm run dev
```

## What You Can Do

The app is fully functional:

1. **Analyze Requirements** - Type a requirement and click "Analyze Requirement"
2. **View Results** - See quality metrics and potential issues
3. **Handle Clarifications** - Answer questions if the AI needs clarification
4. **View Formalized Requirements** - See ISO 29148 formatted results
5. **Export** - Export to Jira, Trello, or PDF (requires backend export setup)

## Development Tips

### Hot Reload
Changes to files are instantly reflected. No manual reload needed.

### TypeScript Errors
Open the terminal - any type errors show up instantly.

### Styling
Edit `src/styles/globals.css` and Tailwind classes in components. Changes apply immediately.

### API Testing
Open browser DevTools → Network tab to see API calls.

## Build for Production

```bash
npm run build
```

Output in `dist/` folder. Deploy to any static host (Netlify, Vercel, GitHub Pages, etc.).

## Troubleshooting

### "Cannot connect to backend"
- Check backend is running on `http://localhost:8000`
- Check no CORS errors in browser console
- Verify backend is serving on correct port

### Port 3000 already in use
```bash
# Use different port
npm run dev -- --port 3001
```

### Module not found errors
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Types errors
```bash
npm run type-check
```

## Next Steps

- **Add more pages**: Create in `src/pages/`
- **Add more components**: Create reusable UI in `src/components/`
- **Extend API**: Add endpoints in `src/services/api.ts`
- **Customize styling**: Edit `tailwind.config.ts`

Enjoy building! 🚀
