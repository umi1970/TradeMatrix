# Current Tasks - Screenshot Analysis Fixes

**Session:** 2025-11-10 (nach Kompaktierung)

---

## 🐛 Problem 1: risk_reward Type Error

**Error:** `item.analysis.risk_reward?.toFixed is not a function`

**Ursache:** Vision gibt `"1:2"` (String) zurück, Frontend erwartet Number

**Lösung:**

### Schritt 1: Prompt Fix
**File:** `apps/web/src/app/api/screenshots/analyze/route.ts`
**Zeile:** ~79 (bei "### 6️⃣ TRADING_SETUP")

**Ändern von:**
```
risk_reward,
```

**Ändern zu:**
```
risk_reward (as decimal number, e.g., 2.0 for 2:1 ratio - NOT string like '1:2'),
```

### Schritt 2: Frontend Safety Check
**File:** `apps/web/src/app/dashboard/screenshots/page.tsx`
**Zeile:** 358

**Ändern von:**
```typescript
<p className="font-mono font-semibold">{item.analysis.risk_reward?.toFixed(1) || 'N/A'}</p>
```

**Ändern zu:**
```typescript
<p className="font-mono font-semibold">
  {typeof item.analysis.risk_reward === 'number'
    ? item.analysis.risk_reward.toFixed(1)
    : item.analysis.risk_reward || 'N/A'}
</p>
```

### Test:
- Upload Screenshot
- Check console: `risk_reward` sollte `2.0` sein (nicht `"1:2"`)
- Frontend sollte `2.0` anzeigen ohne Error

---

## 🐛 Problem 2: Screenshots werden nicht gespeichert

**Ursache:**
- Screenshots nur im Browser (RAM)
- Bezahlen $0.015 pro Analyse, aber Screenshot geht verloren
- Nach Reload: Alles weg

**Lösung:**

### Schritt 1: Supabase Storage Bucket Setup (manuell in Supabase Dashboard)
1. Gehe zu: Supabase Dashboard → Storage
2. Create Bucket: `chart-screenshots`
3. Public: YES (damit Screenshots öffentlich zugänglich sind)
4. File Size Limit: 10MB

### Schritt 2: Backend - Upload zu Storage
**File:** `apps/web/src/app/api/screenshots/analyze/route.ts`
**Nach Zeile:** ~20 (nach `const file = formData.get('file')`)

**Code einfügen:**
```typescript
// Upload screenshot to Supabase Storage
const timestamp = Date.now()
const fileName = `${timestamp}_${file.name}`
const filePath = `screenshots/${fileName}`

const { data: uploadData, error: uploadError } = await supabase
  .storage
  .from('chart-screenshots')
  .upload(filePath, file, {
    contentType: file.type,
    cacheControl: '3600',
  })

if (uploadError) {
  console.error('❌ Failed to upload screenshot:', uploadError)
  return NextResponse.json(
    { error: 'Failed to upload screenshot' },
    { status: 500 }
  )
}

// Get public URL
const { data: urlData } = supabase
  .storage
  .from('chart-screenshots')
  .getPublicUrl(filePath)

const screenshotUrl = urlData.publicUrl
console.log(`✅ Screenshot uploaded: ${screenshotUrl}`)
```

### Schritt 3: Nutze Storage URL statt 'screenshot'
**File:** Gleiche Datei, Zeile ~218

**Ändern von:**
```typescript
chart_url: 'screenshot',
```

**Ändern zu:**
```typescript
chart_url: screenshotUrl,
```

### Test:
- Upload Screenshot
- Check console: `✅ Screenshot uploaded: https://...`
- Check Supabase Storage: File sollte da sein
- Check DB `chart_analyses.chart_url`: Sollte URL enthalten (nicht 'screenshot')

---

## 🐛 Problem 3: UI zeigt keine History nach Reload

**Ursache:** Screenshots nur in Component State, nicht persistent

**Lösung:**

### Schritt 1: Load Existing Analyses beim Page-Load
**File:** `apps/web/src/app/dashboard/screenshots/page.tsx`
**Nach Zeile:** ~41 (nach `const [uploading, setUploading] = useState(false)`)

**Code einfügen:**
```typescript
const [loading, setLoading] = useState(true)

useEffect(() => {
  loadExistingAnalyses()
}, [])

const loadExistingAnalyses = async () => {
  try {
    // Fetch recent analyses from DB that have screenshot URLs
    const response = await fetch('/api/screenshots/history?limit=50')
    const data = await response.json()

    if (response.ok && data.analyses) {
      // Convert DB analyses to AnalysisResult format
      const existingAnalyses: AnalysisResult[] = data.analyses.map((dbAnalysis: any) => ({
        file: null, // No file object for existing analyses
        status: 'success' as const,
        analysis: {
          analysis_id: dbAnalysis.id,
          symbol: dbAnalysis.payload.symbol,
          timeframe: dbAnalysis.timeframe,
          current_price: dbAnalysis.payload.current_price,
          trend: dbAnalysis.trend,
          trend_strength: dbAnalysis.payload.trend_strength,
          price_vs_emas: dbAnalysis.payload.price_vs_emas,
          momentum_bias: dbAnalysis.payload.momentum_bias,
          confidence_score: dbAnalysis.confidence_score,
          chart_quality: dbAnalysis.payload.chart_quality,
          key_factors: dbAnalysis.payload.key_factors,
          setup_type: dbAnalysis.payload.setup_type,
          entry_price: dbAnalysis.payload.entry_price,
          stop_loss: dbAnalysis.payload.stop_loss,
          take_profit: dbAnalysis.payload.take_profit,
          risk_reward: dbAnalysis.payload.risk_reward,
          reasoning: dbAnalysis.analysis_summary,
          timeframe_validity: dbAnalysis.payload.timeframe_validity,
          patterns_detected: dbAnalysis.patterns_detected,
          support_levels: dbAnalysis.support_levels,
          resistance_levels: dbAnalysis.resistance_levels,
        },
        screenshot_url: dbAnalysis.chart_url, // Add this field!
      }))

      setFiles(existingAnalyses)
    }
  } catch (error) {
    console.error('Failed to load existing analyses:', error)
  } finally {
    setLoading(false)
  }
}
```

### Schritt 2: Update AnalysisResult Interface
**File:** Gleiche Datei, Zeile ~10

**Ändern von:**
```typescript
interface AnalysisResult {
  file: File
  status: 'pending' | 'analyzing' | 'success' | 'error'
  analysis?: {...}
  error?: string
}
```

**Ändern zu:**
```typescript
interface AnalysisResult {
  file: File | null  // Allow null for existing analyses
  status: 'pending' | 'analyzing' | 'success' | 'error'
  analysis?: {...}
  error?: string
  screenshot_url?: string  // For existing analyses from DB
}
```

### Schritt 3: Display Screenshot from URL or File
**File:** Gleiche Datei, CardContent section (Zeile ~250)

**Vor dem Analysis-Content einfügen:**
```typescript
{/* Screenshot Image */}
{(item.screenshot_url || item.file) && (
  <div className="mb-3">
    <img
      src={item.screenshot_url || URL.createObjectURL(item.file!)}
      alt={`Chart ${item.analysis?.symbol}`}
      className="w-full h-48 object-contain bg-muted rounded"
    />
  </div>
)}
```

### Schritt 4: Create History API Endpoint
**File:** `apps/web/src/app/api/screenshots/history/route.ts` (NEU!)

**Content:**
```typescript
import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const limit = parseInt(searchParams.get('limit') || '50')

    // Get analyses that have screenshot URLs (not 'screenshot' dummy value)
    const { data, error } = await supabase
      .from('chart_analyses')
      .select(`
        id,
        symbol_id,
        timeframe,
        chart_url,
        patterns_detected,
        trend,
        support_levels,
        resistance_levels,
        confidence_score,
        analysis_summary,
        payload,
        created_at,
        market_symbols (
          symbol,
          name
        )
      `)
      .not('chart_url', 'eq', 'screenshot')
      .order('created_at', { ascending: false })
      .limit(limit)

    if (error) {
      console.error('Failed to fetch analyses:', error)
      return NextResponse.json(
        { error: 'Failed to fetch analyses' },
        { status: 500 }
      )
    }

    return NextResponse.json({
      analyses: data || [],
      count: data?.length || 0,
    })

  } catch (error) {
    console.error('History API error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch history' },
      { status: 500 }
    )
  }
}
```

### Test:
- Reload page
- Should see loading spinner
- Should load existing analyses from DB
- Should show screenshots from Supabase Storage URLs
- New uploads should appear at top of list

---

## 📋 Reihenfolge:

1. **Problem 1** (2 Min) - Schneller Fix, blockiert nichts
2. **Problem 2** (10 Min) - Storage Setup + Backend Integration
3. **Problem 3** (15 Min) - Frontend UI für History

**Total:** ~27 Minuten

---

## 🚨 Wichtig:

- **ERST PLAN SAGEN, DANN CODE SCHREIBEN!**
- **Keine Commits/Pushes ohne Erlaubnis!**
- Dev-Server läuft lokal

---

## Status: ⏸️ Waiting for Approval

User kompaktiert Session. Nach Kompaktierung: Diese Datei lesen und weiter machen!
