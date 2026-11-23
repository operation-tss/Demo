import React, { useState, useMemo, useRef, useEffect } from 'react';
import { 
  X, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  Calendar, 
  Database, 
  AlertCircle, 
  Activity, 
  CheckCircle2, 
  Clock
} from 'lucide-react';

/**
 * Robust parameter name and alias matching helper.
 * Strictly separates distinct medical parameters (e.g., Hemoglobin vs MCH vs MCHC).
 */
const CANONICAL_GROUPS = [
  { key: 'mchc', aliases: ['mchc', 'mean corpuscular hemoglobin concentration'] },
  { key: 'mch', aliases: ['mch', 'mean corpuscular hemoglobin'] },
  { key: 'mcv', aliases: ['mcv', 'mean corpuscular volume'] },
  { key: 'hemoglobin', aliases: ['hemoglobin', 'haemoglobin', 'hb', 'hgb'] },
  { key: 'pcv', aliases: ['pcv', 'packed cell volume', 'hematocrit', 'hct', 'packed cell volume (pcv)'] },
  { key: 'rbc', aliases: ['rbc', 'total rbc count', 'red blood cell count', 'erythrocytes', 'total rbc'] },
  { key: 'wbc', aliases: ['wbc', 'total leukocyte count', 'total white blood cells', 'leukocyte', 'total leukocyte count (wbc)', 'tlc'] },
  { key: 'platelets', aliases: ['platelets', 'platelet count', 'plt', 'total platelet count'] },
  { key: 'glucose', aliases: ['glucose', 'blood glucose', 'fasting blood sugar', 'fbs', 'rbs', 'random blood sugar', 'blood glucose fasting', 'blood sugar'] },
  { key: 'cholesterol', aliases: ['cholesterol', 'total cholesterol', 'serum cholesterol'] },
  { key: 'direct_bilirubin', aliases: ['direct bilirubin', 'conjugated bilirubin', 'bilirubin direct'] },
  { key: 'total_bilirubin', aliases: ['total bilirubin', 'bilirubin total', 'serum bilirubin total', 'bilirubin'] },
  { key: 'sgpt', aliases: ['sgpt', 'alt', 'alanine aminotransferase', 'sgpt / alt', 'sgpt/alt'] },
  { key: 'sgot', aliases: ['sgot', 'ast', 'aspartate aminotransferase', 'sgot / ast', 'sgot/ast'] },
  { key: 'alp', aliases: ['alp', 'alkaline phosphatase', 'alkaline phosphatase (alp)'] },
  { key: 'bun', aliases: ['bun', 'blood urea nitrogen'] },
  { key: 'creatinine', aliases: ['creatinine', 'serum creatinine'] },
  { key: 'albumin', aliases: ['albumin', 'serum albumin'] },
];

function getCanonicalKey(rawName) {
  if (!rawName) return null;
  const clean = rawName.toLowerCase().replace(/[^a-z0-9]/g, ' ').trim().replace(/\s+/g, ' ');
  const words = clean.split(' ');
  for (const group of CANONICAL_GROUPS) {
    for (const alias of group.aliases) {
      const cleanAlias = alias.toLowerCase().replace(/[^a-z0-9]/g, ' ').trim().replace(/\s+/g, ' ');
      if (clean === cleanAlias) {
        return group.key;
      }
      if (cleanAlias.includes(' ')) {
        if (` ${clean} `.includes(` ${cleanAlias} `)) {
          return group.key;
        }
      } else {
        if (words.includes(cleanAlias)) {
          return group.key;
        }
      }
    }
  }
  return clean;
}

function isParameterMatch(recName, targetName, recParamId, targetParamId) {
  if (targetParamId && recParamId) {
    return Number(recParamId) === Number(targetParamId);
  }

  if (!recName || !targetName) return false;

  const keyA = getCanonicalKey(recName);
  const keyB = getCanonicalKey(targetName);

  if (keyA && keyB) {
    return keyA === keyB;
  }

  const a = recName.toLowerCase().trim();
  const b = targetName.toLowerCase().trim();
  return a === b;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function formatFullDate(dateStr) {
  if (!dateStr) return '—';
  try {
    const parts = String(dateStr).split('T')[0].split('-');
    if (parts.length === 3) {
      const [y, m, d] = parts;
      const mIdx = parseInt(m, 10) - 1;
      const mName = MONTHS[mIdx] || m;
      return `${parseInt(d, 10)} ${mName} ${y}`;
    }
    return dateStr;
  } catch {
    return dateStr;
  }
}

function formatShortDate(dateStr) {
  if (!dateStr) return '';
  try {
    const parts = String(dateStr).split('T')[0].split('-');
    if (parts.length === 3) {
      const [, m, d] = parts;
      const mIdx = parseInt(m, 10) - 1;
      const mName = MONTHS[mIdx] || m;
      return `${parseInt(d, 10)} ${mName}`;
    }
    return dateStr;
  } catch {
    return dateStr;
  }
}

function formatYear(dateStr) {
  if (!dateStr) return '';
  try {
    const parts = String(dateStr).split('T')[0].split('-');
    return parts[0] || '';
  } catch {
    return '';
  }
}

function formatDateTime(dtStr) {
  if (!dtStr) return '—';
  try {
    const s = String(dtStr).replace('Z', '');
    const [dPart, tPart] = s.split('T');
    const parts = dPart.split('-');
    if (parts.length === 3) {
      const [y, m, d] = parts;
      const mIdx = parseInt(m, 10) - 1;
      const mName = MONTHS[mIdx] || m;
      const timeClean = tPart ? tPart.split('.')[0] : '';
      return `${parseInt(d, 10)} ${mName} ${y}${timeClean ? ' ' + timeClean : ''}`;
    }
    return dtStr;
  } catch {
    return dtStr;
  }
}

/**
 * ParameterTrendChart (formerly ParameterTrendModal)
 * Displays chronological line chart for any selected lab parameter.
 * - Dynamic Y-axis min/max calculation with 28% margin.
 * - Exact date association for every point with vertical stems and X-axis ticks.
 * - Interactive hover and click tooltips with full report date, parameter, value, and unit.
 * - Pinned Y-axis panel for smooth horizontal scrolling over 100+ readings.
 * - Compact date-wise readings history table with stable hover behavior.
 */
export const ParameterTrendChart = ({
  isOpen = false,
  onClose,
  parameterName = '',
  parameterId = null,
  patient = null,
  timelineRecords = [],
  unit = '',
  referenceRange = '',
  currentValue = '',
  currentStatus = '',
  reportDate = '',
  isLoading: _isLoading = false,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const [selectedPoint, setSelectedPoint] = useState(null);

  // Reset hover and selection when modal opens or parameter changes
  const currentKey = `${parameterName}_${parameterId}_${isOpen}`;
  const [prevKey, setPrevKey] = useState(currentKey);
  if (currentKey !== prevKey) {
    setPrevKey(currentKey);
    setHoveredPoint(null);
    setSelectedPoint(null);
  }

  // Extract and sort numeric data points chronologically
  const chartPoints = useMemo(() => {
    let matching = [];

    if (timelineRecords && timelineRecords.length > 0) {
      matching = timelineRecords.filter((rec) =>
        isParameterMatch(rec.parameter_name, parameterName, rec.parameter_id, parameterId)
      );
    }

    // Parse numeric values and dates
    const parsed = matching
      .map((rec) => {
        const rawVal = rec.test_result || rec.value || '';
        const numVal = parseFloat(String(rawVal).replace(/[^\d.-]/g, ''));
        const dateStr = rec.report_date ? String(rec.report_date).split('T')[0] : '';
        return {
          id: rec.timeline_id,
          date: dateStr,
          rawVal: String(rawVal),
          val: isNaN(numVal) ? null : numVal,
          unit: rec.unit || unit,
          refRange: rec.reference_range || referenceRange,
          status: rec.status || 'NORMAL',
          savedOn: rec.saved_on,
          isCurrentOnly: false,
        };
      })
      .filter((p) => p.val !== null);

    // If no historical records exist in MSSQL timeline, display current report's actual reading
    if (parsed.length === 0 && currentValue) {
      const numVal = parseFloat(String(currentValue).replace(/[^\d.-]/g, ''));
      if (!isNaN(numVal)) {
        parsed.push({
          id: 'current-reading',
          date: reportDate ? String(reportDate).split('T')[0] : 'Current Report',
          rawVal: String(currentValue),
          val: numVal,
          unit: unit,
          refRange: referenceRange,
          status: currentStatus || 'NORMAL',
          isCurrentOnly: true,
        });
      }
    }

    // Sort chronologically by date
    parsed.sort((a, b) => new Date(a.date || 0) - new Date(b.date || 0));
    return parsed;
  }, [timelineRecords, parameterName, parameterId, unit, referenceRange, currentValue, currentStatus, reportDate]);

  // Parse reference range bounds if available (e.g., "13.0 - 17.0", "70 - 140")
  const refBounds = useMemo(() => {
    const rangeStr = referenceRange || (chartPoints.length > 0 ? chartPoints[0].refRange : '');
    if (!rangeStr) return null;
    const match = rangeStr.match(/(\d+(?:\.\d+)?)\s*[-–to]\s*(\d+(?:\.\d+)?)/i);
    if (match) {
      const low = parseFloat(match[1]);
      const high = parseFloat(match[2]);
      if (!isNaN(low) && !isNaN(high)) {
        return { low, high };
      }
    }
    return null;
  }, [referenceRange, chartPoints]);

  // Trend analysis (difference between first and latest reading)
  const trendAnalysis = useMemo(() => {
    if (chartPoints.length < 2) return null;
    const first = chartPoints[0].val;
    const latest = chartPoints[chartPoints.length - 1].val;
    const diff = latest - first;
    const pct = first !== 0 ? (diff / first) * 100 : 0;
    return {
      diff: parseFloat(diff.toFixed(2)),
      pct: parseFloat(pct.toFixed(1)),
      direction: diff > 0.05 ? 'up' : diff < -0.05 ? 'down' : 'stable',
    };
  }, [chartPoints]);

  // Container & Scroll references
  const scrollContainerRef = useRef(null);

  // SVG Chart Geometry
  const height = 280;
  const paddingTop = 40;
  const paddingBottom = 60;
  const chartH = height - paddingTop - paddingBottom; // 180px

  // Dynamic Horizontal Width: supports 100+ points without truncation or crowding
  const minPointSpacing = 68; // px between data points (prevents overlapping labels, values, and 32px targets)
  const plotPaddingLeft = 45;
  const plotPaddingRight = 55;
  const dynamicPlotW = chartPoints.length > 1
    ? (chartPoints.length - 1) * minPointSpacing + plotPaddingLeft + plotPaddingRight
    : 600;
  const plotWidth = Math.max(600, dynamicPlotW);

  // Calculate Y-scale bounds
  let minY = 0;
  let maxY = 100;

  if (chartPoints.length > 0) {
    const values = chartPoints.map((p) => p.val);
    if (refBounds) {
      values.push(refBounds.low, refBounds.high);
    }
    const dataMin = Math.min(...values);
    const dataMax = Math.max(...values);
    const span = dataMax - dataMin;
    const margin = span > 0 ? span * 0.28 : dataMax > 0 ? dataMax * 0.28 : 5;
    minY = Math.max(0, parseFloat((dataMin - margin).toFixed(1)));
    maxY = parseFloat((dataMax + margin).toFixed(1));

    if (maxY <= minY) {
      minY = Math.max(0, minY - 5);
      maxY = maxY + 5;
    }
  }

  const getYCoord = (val) => {
    if (maxY === minY) return paddingTop + chartH / 2;
    return paddingTop + chartH - ((val - minY) / (maxY - minY)) * chartH;
  };

  const getXCoord = (idx) => {
    if (chartPoints.length <= 1) return plotWidth / 2;
    return plotPaddingLeft + idx * ((plotWidth - plotPaddingLeft - plotPaddingRight) / (chartPoints.length - 1));
  };

  // Auto-scroll to latest (rightmost) reading on open or parameter change
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollLeft = scrollContainerRef.current.scrollWidth;
    }
  }, [parameterName, parameterId, isOpen, chartPoints.length]);

  // Build SVG Path for 2 or more points
  const linePath = chartPoints.length >= 2
    ? chartPoints
        .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getXCoord(i)} ${getYCoord(p.val)}`)
        .join(' ')
    : '';

  // Area under path
  const areaPath = chartPoints.length >= 2 && linePath
    ? `${linePath} L ${getXCoord(chartPoints.length - 1)} ${paddingTop + chartH} L ${getXCoord(0)} ${paddingTop + chartH} Z`
    : '';

  if (!isOpen) return null;

  const latestPoint = chartPoints.length > 0 ? chartPoints[chartPoints.length - 1] : null;
  const displayVal = currentValue || latestPoint?.rawVal || '—';
  const displayUnit = unit || latestPoint?.unit || '';
  const displayRange = referenceRange || latestPoint?.refRange || '';
  const displayStatus = currentStatus || latestPoint?.status || 'NORMAL';

  // Active point for inspection: ONLY when intentionally hovered or clicked
  const activePoint = hoveredPoint || selectedPoint || null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto animate-fade-in">
      <div 
        className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden my-auto"
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-800 flex items-center justify-center shadow-xs">
              <Activity className="w-5 h-5 text-blue-700" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900">{parameterName}</h3>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200">
                  Historical Trend Chart
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Patient: <strong className="text-slate-800">{patient?.patient_name || 'Selected Patient'}</strong>{' '}
                {patient?.health_id && `(${patient.health_id})`} • Source: MSSQL Timeline
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg hover:bg-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1">
          {/* Key Metric Highlights Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <p className="text-[11px] font-bold text-slate-500 uppercase">Latest Observed Value</p>
              <p className="text-lg font-black text-slate-900 mt-0.5">
                {displayVal}{' '}
                <span className="text-xs font-normal text-slate-500">{displayUnit}</span>
              </p>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <p className="text-[11px] font-bold text-slate-500 uppercase">Reference Range</p>
              <p className="text-sm font-bold text-slate-800 mt-1">
                {displayRange ? `${displayRange} ${displayUnit}` : 'Standard Clinical'}
              </p>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <p className="text-[11px] font-bold text-slate-500 uppercase">Recorded Data Points</p>
              <p className="text-sm font-black text-blue-700 mt-1">
                {chartPoints.length} {chartPoints.length === 1 ? 'Reading' : 'Readings'}
              </p>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <p className="text-[11px] font-bold text-slate-500 uppercase">Clinical Status</p>
              <div className="mt-1">
                <span className={`inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full ${
                  displayStatus === 'HIGH' ? 'bg-rose-100 text-rose-800' :
                  displayStatus === 'LOW' ? 'bg-blue-100 text-blue-800' :
                  'bg-emerald-100 text-emerald-800'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    displayStatus === 'HIGH' ? 'bg-rose-600' :
                    displayStatus === 'LOW' ? 'bg-blue-600' :
                    'bg-emerald-600'
                  }`} />
                  {displayStatus}
                </span>
              </div>
            </div>
          </div>

          {/* Graph Visualization Container */}
          <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-600" />
                <span className="text-xs font-bold text-slate-800">
                  {parameterName} Chronological Graph ({displayUnit || 'Standard'})
                </span>
                <span className="text-[11px] text-slate-400 font-medium">
                  • Click or hover any point to view exact report details
                </span>
              </div>

              {trendAnalysis && (
                <div className="flex items-center gap-1 text-xs font-bold">
                  {trendAnalysis.direction === 'up' && (
                    <span className="flex items-center gap-1 text-rose-600 bg-rose-50 px-2 py-0.5 rounded-md border border-rose-200">
                      <TrendingUp className="w-3.5 h-3.5" />
                      <span>+{trendAnalysis.diff} ({trendAnalysis.pct}%)</span>
                    </span>
                  )}
                  {trendAnalysis.direction === 'down' && (
                    <span className="flex items-center gap-1 text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200">
                      <TrendingDown className="w-3.5 h-3.5" />
                      <span>{trendAnalysis.diff} ({trendAnalysis.pct}%)</span>
                    </span>
                  )}
                  {trendAnalysis.direction === 'stable' && (
                    <span className="flex items-center gap-1 text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md">
                      <Minus className="w-3.5 h-3.5" />
                      <span>Stable trajectory</span>
                    </span>
                  )}
                </div>
              )}
            </div>

            {chartPoints.length > 0 ? (
              <div className="relative">
                {/* Dynamic Horizontal Scroll Graph Container with Pinned Y-Axis & Reference Range */}
                <div className="relative flex border border-slate-200 rounded-2xl bg-white overflow-hidden shadow-xs">
                  {/* Pinned Left Y-Axis Panel (permanently visible during horizontal scrolling) */}
                  <div className="w-16 sm:w-20 shrink-0 bg-slate-50/95 border-r border-slate-200 z-20 select-none flex flex-col justify-between">
                    <svg width="100%" height={height} viewBox="0 0 76 280" className="overflow-visible">
                      {/* Y-Axis Unit */}
                      <text x={70} y={22} textAnchor="end" className="text-[10px] fill-slate-500 font-mono font-medium">
                        {displayUnit || 'Val'}
                      </text>
                      {/* Vertical Axis line */}
                      <line x1={75.5} y1={paddingTop} x2={75.5} y2={paddingTop + chartH} stroke="#cbd5e1" strokeWidth="1.5" />
                      {/* 5 Grid Tick Levels */}
                      {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
                        const yVal = minY + (maxY - minY) * (1 - ratio);
                        const y = paddingTop + chartH * ratio;
                        return (
                          <g key={ratio}>
                            <line x1={68} y1={y} x2={75.5} y2={y} stroke="#94a3b8" strokeWidth="1" />
                            <text x={64} y={y + 3.5} textAnchor="end" className="text-[10px] fill-slate-500 font-mono font-medium">
                              {yVal.toFixed(1)}
                            </text>
                          </g>
                        );
                      })}
                      {/* Reference Range Pinned Indicators on Y-Axis */}
                      {refBounds && (
                        <g>
                          <line x1={56} y1={getYCoord(refBounds.high)} x2={75.5} y2={getYCoord(refBounds.high)} stroke="#10b981" strokeWidth="1.5" strokeDasharray="3 2" />
                          <text x={53} y={getYCoord(refBounds.high) + 3} textAnchor="end" className="text-[8px] fill-emerald-700 font-bold">
                            Max
                          </text>
                          <line x1={56} y1={getYCoord(refBounds.low)} x2={75.5} y2={getYCoord(refBounds.low)} stroke="#10b981" strokeWidth="1.5" strokeDasharray="3 2" />
                          <text x={53} y={getYCoord(refBounds.low) + 3} textAnchor="end" className="text-[8px] fill-emerald-700 font-bold">
                            Min
                          </text>
                        </g>
                      )}
                    </svg>
                  </div>

                  {/* Horizontally Scrollable Plot Area (Supports 100+ points without truncation) */}
                  <div 
                    ref={scrollContainerRef}
                    className="flex-1 overflow-x-auto relative select-none scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-slate-100"
                  >
                    <svg 
                      width={plotWidth} 
                      height={height} 
                      viewBox={`0 0 ${plotWidth} ${height}`} 
                      className="block select-none"
                      onMouseLeave={() => setHoveredPoint(null)}
                    >
                      <defs>
                        <linearGradient id="parameterTrendGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#2563eb" stopOpacity="0.25" />
                          <stop offset="100%" stopColor="#2563eb" stopOpacity="0.0" />
                        </linearGradient>
                        <filter id="pointShadow" x="-20%" y="-20%" width="140%" height="140%">
                          <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.2" />
                        </filter>
                      </defs>

                      {/* Horizontal Grid Lines extending across full plotWidth */}
                      {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
                        const y = paddingTop + chartH * ratio;
                        return (
                          <line
                            key={ratio}
                            x1={0}
                            y1={y}
                            x2={plotWidth}
                            y2={y}
                            stroke="#f1f5f9"
                            strokeWidth="1"
                          />
                        );
                      })}

                      {/* Shaded Reference Range Normal Zone extending across full plotWidth */}
                      {refBounds && (
                        <g>
                          <rect
                            x={0}
                            y={Math.min(getYCoord(refBounds.high), getYCoord(refBounds.low))}
                            width={plotWidth}
                            height={Math.max(2, Math.abs(getYCoord(refBounds.high) - getYCoord(refBounds.low)))}
                            fill="#10b981"
                            fillOpacity="0.08"
                          />
                          <line
                            x1={0}
                            y1={getYCoord(refBounds.high)}
                            x2={plotWidth}
                            y2={getYCoord(refBounds.high)}
                            stroke="#10b981"
                            strokeWidth="1"
                            strokeDasharray="4 3"
                            strokeOpacity="0.7"
                          />
                          <line
                            x1={0}
                            y1={getYCoord(refBounds.low)}
                            x2={plotWidth}
                            y2={getYCoord(refBounds.low)}
                            stroke="#10b981"
                            strokeWidth="1"
                            strokeDasharray="4 3"
                            strokeOpacity="0.7"
                          />
                          <text
                            x={plotWidth - 10}
                            y={getYCoord(refBounds.high) - 4}
                            textAnchor="end"
                            className="text-[9px] fill-emerald-600 font-bold"
                          >
                            Normal Max: {refBounds.high} {displayUnit}
                          </text>
                          <text
                            x={plotWidth - 10}
                            y={getYCoord(refBounds.low) + 11}
                            textAnchor="end"
                            className="text-[9px] fill-emerald-600 font-bold"
                          >
                            Normal Min: {refBounds.low} {displayUnit}
                          </text>
                        </g>
                      )}

                      {/* Gradient Area Fill (for 2+ points) */}
                      {areaPath && <path d={areaPath} fill="url(#parameterTrendGradient)" />}

                      {/* Trend Line (for 2+ points) */}
                      {linePath && (
                        <path
                          d={linePath}
                          fill="none"
                          stroke="#2563eb"
                          strokeWidth="3"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      )}

                      {/* X-Axis Horizontal Base Line extending across full plotWidth */}
                      <line
                        x1={0}
                        y1={paddingTop + chartH}
                        x2={plotWidth}
                        y2={paddingTop + chartH}
                        stroke="#cbd5e1"
                        strokeWidth="1.5"
                      />

                      {/* Render Clear Association: Vertical Stems, X-Axis Ticks & 2-Tier Date Labels */}
                      {chartPoints.map((pt, idx) => {
                        const cx = getXCoord(idx);
                        const cy = getYCoord(pt.val);
                        const isHovered = hoveredPoint?.id === pt.id;
                        const isSelected = selectedPoint?.id === pt.id;
                        const isActive = isHovered || isSelected;

                        return (
                          <g key={`stem-${pt.id || idx}`}>
                            {/* Vertical Stem Line from point to X-axis */}
                            <line
                              x1={cx}
                              y1={cy + 8}
                              x2={cx}
                              y2={paddingTop + chartH}
                              stroke={isActive ? '#2563eb' : '#e2e8f0'}
                              strokeWidth={isActive ? '2' : '1'}
                              strokeDasharray={isActive ? 'none' : '3 3'}
                              strokeOpacity={isActive ? '1' : '0.8'}
                              pointerEvents="none"
                              style={{ pointerEvents: 'none' }}
                            />

                            {/* X-Axis Tick Line */}
                            <line
                              x1={cx}
                              y1={paddingTop + chartH}
                              x2={cx}
                              y2={paddingTop + chartH + 5}
                              stroke={isActive ? '#1d4ed8' : '#94a3b8'}
                              strokeWidth={isActive ? '2' : '1.5'}
                              pointerEvents="none"
                              style={{ pointerEvents: 'none' }}
                            />

                            {/* Date Label: Line 1 (Day + Month) */}
                            <text
                              x={cx}
                              y={paddingTop + chartH + 18}
                              textAnchor="middle"
                              className={`text-[11px] font-bold tracking-tight cursor-pointer ${
                                isActive ? 'fill-blue-700 font-extrabold' : 'fill-slate-700'
                              }`}
                              onClick={() => setSelectedPoint((prev) => (prev?.id === pt.id ? null : pt))}
                            >
                              {formatShortDate(pt.date)}
                            </text>

                            {/* Date Label: Line 2 (Year) */}
                            <text
                              x={cx}
                              y={paddingTop + chartH + 30}
                              textAnchor="middle"
                              className={`text-[9px] font-medium ${
                                isActive ? 'fill-blue-600 font-bold' : 'fill-slate-400'
                              }`}
                              pointerEvents="none"
                              style={{ pointerEvents: 'none' }}
                            >
                              {formatYear(pt.date)}
                            </text>

                            <title>{`${parameterName}: ${pt.rawVal} ${pt.unit} on ${pt.date}`}</title>
                          </g>
                        );
                      })}

                      {/* Render Data Points & Stable Hit Targets */}
                      {chartPoints.map((pt, idx) => {
                        const cx = getXCoord(idx);
                        const cy = getYCoord(pt.val);
                        const isHovered = hoveredPoint?.id === pt.id;
                        const isSelected = selectedPoint?.id === pt.id;
                        const isActive = isHovered || isSelected;

                        return (
                          <g key={`pt-${pt.id || idx}`}>
                            {/* Visual Highlight Ring (shown only when active) */}
                            {isActive && (
                              <circle
                                cx={cx}
                                cy={cy}
                                r={chartPoints.length === 1 ? 16 : 13}
                                fill="#2563eb"
                                fillOpacity={0.22}
                                pointerEvents="none"
                                style={{ pointerEvents: 'none' }}
                              />
                            )}

                            {/* Visual Data Point Circle */}
                            <circle
                              cx={cx}
                              cy={cy}
                              r={isActive ? 6.5 : 5}
                              fill={isActive ? '#1d4ed8' : '#ffffff'}
                              stroke="#2563eb"
                              strokeWidth="2.5"
                              filter="url(#pointShadow)"
                              pointerEvents="none"
                              style={{ pointerEvents: 'none' }}
                            />

                            {/* Numeric Value Label above circle */}
                            <text
                              x={cx}
                              y={cy - 12}
                              textAnchor="middle"
                              pointerEvents="none"
                              style={{ pointerEvents: 'none' }}
                              className={`text-xs font-black select-none ${
                                isActive ? 'fill-blue-900 font-extrabold text-sm' : 'fill-slate-900'
                              }`}
                            >
                              {pt.rawVal}
                            </text>

                            {/* Stable Fixed-Radius Hit Area (32px diameter) */}
                            {/* Never resizes, prevents all mouseleave/mouseenter flickering */}
                            <circle
                              cx={cx}
                              cy={cy}
                              r={16}
                              fill="transparent"
                              cursor="pointer"
                              pointerEvents="all"
                              onMouseEnter={() => {
                                if (hoveredPoint?.id !== pt.id) {
                                  setHoveredPoint(pt);
                                }
                              }}
                              onMouseLeave={() => setHoveredPoint((prev) => (prev?.id === pt.id ? null : prev))}
                              onClick={() => setSelectedPoint((prev) => (prev?.id === pt.id ? null : pt))}
                            />
                          </g>
                        );
                      })}

                      {/* Floating SVG Tooltip Card - Shown ONLY when active (hovered or clicked) */}
                      {activePoint && (() => {
                        const idx = chartPoints.findIndex((p) => p.id === activePoint.id);
                        if (idx === -1) return null;
                        const cx = getXCoord(idx);
                        const cy = getYCoord(activePoint.val);

                        // Clamp tooltip horizontal position within scrollable plot area
                        const tipW = 180;
                        const tipH = activePoint.savedOn ? 66 : 54;
                        const tipX = Math.max(10, Math.min(plotWidth - tipW - 10, cx - tipW / 2));
                        const tipY = cy > paddingTop + tipH + 20 ? cy - tipH - 18 : cy + 20;

                        return (
                          <g 
                            pointerEvents="none" 
                            style={{ pointerEvents: 'none' }} 
                            className="animate-fade-in"
                          >
                            {/* Tooltip Background Card */}
                            <rect
                              x={tipX}
                              y={tipY}
                              width={tipW}
                              height={tipH}
                              rx={8}
                              fill="#0f172a"
                              fillOpacity="0.96"
                              stroke="#38bdf8"
                              strokeWidth="1.5"
                              pointerEvents="none"
                              style={{ pointerEvents: 'none' }}
                            />
                            {/* Full Report Date */}
                            <text
                              x={tipX + tipW / 2}
                              y={tipY + 16}
                              textAnchor="middle"
                              className="text-[10px] fill-slate-200 font-semibold select-none"
                              pointerEvents="none"
                              style={{ pointerEvents: 'none' }}
                            >
                              📅 Report Date: {formatFullDate(activePoint.date)}
                            </text>
                            {/* Parameter & Observed Value */}
                            <text
                              x={tipX + tipW / 2}
                              y={tipY + 32}
                              textAnchor="middle"
                              className="text-[12px] fill-white font-black select-none"
                              pointerEvents="none"
                              style={{ pointerEvents: 'none' }}
                            >
                              {parameterName}: {activePoint.rawVal} {activePoint.unit}
                            </text>
                            {/* Status */}
                            <text
                              x={tipX + tipW / 2}
                              y={tipY + 45}
                              textAnchor="middle"
                              className={`text-[9px] font-bold select-none ${
                                activePoint.status === 'HIGH' ? 'fill-rose-400' :
                                activePoint.status === 'LOW' ? 'fill-blue-400' :
                                'fill-emerald-400'
                              }`}
                              pointerEvents="none"
                              style={{ pointerEvents: 'none' }}
                            >
                              ● {activePoint.status} {activePoint.refRange ? `(${activePoint.refRange})` : ''}
                            </text>
                            {/* Upload Timestamp */}
                            {activePoint.savedOn && (
                              <text
                                x={tipX + tipW / 2}
                                y={tipY + 58}
                                textAnchor="middle"
                                className="text-[8.5px] fill-slate-400 select-none"
                                pointerEvents="none"
                                style={{ pointerEvents: 'none' }}
                              >
                                Uploaded: {formatDateTime(activePoint.savedOn)}
                              </text>
                            )}
                          </g>
                        );
                      })()}
                    </svg>
                  </div>
                </div>

                {/* Active Reading Inspector Bar */}
                {activePoint ? (
                  <div className="mt-3 p-3 bg-blue-50/70 border border-blue-200 rounded-xl shadow-2xs flex flex-wrap items-center justify-between gap-3 animate-fade-in">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-blue-600 shrink-0" />
                      <div>
                        <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                          Inspected Report Date:
                        </span>
                        <div className="text-xs font-bold text-slate-900">
                          {formatFullDate(activePoint.date)}{' '}
                          <span className="text-[11px] font-mono text-slate-500">({activePoint.date})</span>
                        </div>
                      </div>
                    </div>

                    {activePoint.savedOn && (
                      <div className="flex items-center gap-2">
                        <Clock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        <div>
                          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                            Uploaded On:
                          </span>
                          <div className="text-xs font-bold text-slate-800">
                            {formatDateTime(activePoint.savedOn)}
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="flex items-center gap-3">
                      <div>
                        <span className="text-[11px] font-semibold text-slate-500 uppercase">Parameter: </span>
                        <strong className="text-xs text-slate-900">{parameterName}</strong>
                      </div>
                      <div className="h-4 w-px bg-slate-300 hidden sm:block" />
                      <div>
                        <span className="text-[11px] font-semibold text-slate-500 uppercase">Observed: </span>
                        <span className="text-sm font-black text-blue-700">
                          {activePoint.rawVal} {activePoint.unit}
                        </span>
                      </div>
                      <div className="h-4 w-px bg-slate-300 hidden sm:block" />
                      <div>
                        <span className="text-[11px] font-semibold text-slate-500 uppercase">Status: </span>
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                          activePoint.status === 'HIGH' ? 'bg-rose-100 text-rose-800' :
                          activePoint.status === 'LOW' ? 'bg-blue-100 text-blue-800' :
                          'bg-emerald-100 text-emerald-800'
                        }`}>
                          {activePoint.status}
                        </span>
                      </div>
                    </div>

                    {selectedPoint && (
                      <button
                        type="button"
                        onClick={() => setSelectedPoint(null)}
                        className="text-[11px] font-semibold text-blue-600 hover:text-blue-800 cursor-pointer"
                      >
                        Clear selection
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="mt-3 py-2 px-3 bg-slate-50 border border-slate-200/80 rounded-xl text-center text-xs text-slate-500 flex items-center justify-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                    <span>Hover or click any data point or table row to inspect date-wise reading details</span>
                  </div>
                )}

                {/* Status Ribbon below Chart */}
                <div className="mt-2">
                  {chartPoints[0]?.isCurrentOnly ? (
                    <div className="text-center text-xs font-bold text-amber-800 bg-amber-50 border border-amber-200 py-1.5 px-3 rounded-xl flex items-center justify-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                      <span>Current Report Reading – Not Yet Saved to Timeline</span>
                    </div>
                  ) : chartPoints.length === 1 ? (
                    <div className="text-center text-xs font-semibold text-slate-600 bg-slate-50 border border-slate-200 py-1.5 px-3 rounded-xl flex items-center justify-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                      <span>Single Historical Reading • Recorded on {formatFullDate(chartPoints[0].date)} • Plotted on clinical scale</span>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between text-xs text-slate-600 bg-slate-50 border border-slate-200 py-1.5 px-3 rounded-xl">
                      <span className="flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Chronological line chart with {chartPoints.length} verified readings across {chartPoints.length} dates</span>
                      </span>
                      <span className="font-bold text-blue-800">
                        Trend: {trendAnalysis?.direction === 'up' ? 'Increasing' : trendAnalysis?.direction === 'down' ? 'Decreasing' : 'Stable'}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* Fallback only if no numerical values can be parsed at all */
              <div className="py-12 px-4 text-center bg-slate-50/60 rounded-xl border border-dashed border-slate-200">
                <AlertCircle className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <h4 className="text-sm font-bold text-slate-700">No Numerical Values Found</h4>
                <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                  Unable to plot a numerical chart for <strong>{parameterName}</strong>.
                </p>
              </div>
            )}
          </div>

          {/* Compact Date-Wise Readings History Table */}
          {chartPoints.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-blue-600" />
                  <span>Date-Wise Readings History ({chartPoints.length} Records)</span>
                </h4>
                <span className="text-[11px] text-slate-400 font-medium">
                  Click any row to select & focus corresponding graph point
                </span>
              </div>

              <div className="border border-slate-200 rounded-xl overflow-hidden shadow-2xs max-h-80 overflow-y-auto">
                <table className="w-full text-xs text-left">
                  <thead className="sticky top-0 bg-slate-50 border-b border-slate-200 text-slate-600 font-bold text-[11px] uppercase tracking-wider z-10">
                    <tr>
                      <th className="py-2.5 px-3 w-10 text-center">#</th>
                      <th className="py-2.5 px-3 w-[24%]">Exact Report Date</th>
                      <th className="py-2.5 px-3 w-[20%]">Uploaded Timestamp</th>
                      <th className="py-2.5 px-3 w-[18%]">Parameter</th>
                      <th className="py-2.5 px-3 w-[16%]">Observed Value</th>
                      <th className="py-2.5 px-3 w-[12%]">Reference Range</th>
                      <th className="py-2.5 px-3 w-[10%] text-right">Clinical Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {chartPoints.map((item, idx) => {
                      const isSelected = selectedPoint?.id === item.id;

                      // Calculate change from previous reading if available
                      let deltaText = null;
                      if (idx > 0 && typeof chartPoints[idx - 1].val === 'number') {
                        const diff = item.val - chartPoints[idx - 1].val;
                        if (Math.abs(diff) > 0.01) {
                          deltaText = diff > 0 ? `+${diff.toFixed(2)}` : diff.toFixed(2);
                        }
                      }

                      return (
                        <tr 
                          key={item.id} 
                          onClick={() => {
                            setSelectedPoint((prev) => (prev?.id === item.id ? null : item));
                            if (scrollContainerRef.current) {
                              const targetX = getXCoord(idx);
                              scrollContainerRef.current.scrollTo({ left: Math.max(0, targetX - 250), behavior: 'smooth' });
                            }
                          }}
                          className={`cursor-pointer select-none border-l-4 ${
                            isSelected 
                              ? 'bg-blue-50/90 border-l-blue-600' 
                              : 'border-l-transparent hover:bg-slate-50'
                          }`}
                          title="Click to select and scroll to this report date in the graph"
                        >
                          {/* Index # */}
                          <td className="py-2.5 px-3 text-center text-slate-400 font-mono text-[11px]">
                            {idx + 1}
                          </td>

                          {/* Full Report Date */}
                          <td className="py-2.5 px-3">
                            <div className="flex items-center gap-1.5">
                              <span className="font-bold text-slate-900">
                                {formatFullDate(item.date)}
                              </span>
                              <span className="text-[10px] text-slate-400 font-mono">
                                ({item.date})
                              </span>
                            </div>
                          </td>

                          {/* Uploaded Timestamp */}
                          <td className="py-2.5 px-3">
                            <span className="text-[10px] font-mono text-slate-500">
                              {item.savedOn ? formatDateTime(item.savedOn) : '—'}
                            </span>
                          </td>

                          {/* Parameter Name */}
                          <td className="py-2.5 px-3 text-slate-700 font-semibold">
                            {parameterName}
                          </td>

                          {/* Observed Value & Unit */}
                          <td className="py-2.5 px-3">
                            <div className="flex items-center gap-2">
                              <span className="font-black text-blue-700 text-sm">
                                {item.rawVal} {item.unit}
                              </span>
                              {deltaText && (
                                <span className={`text-[10px] font-bold ${
                                  deltaText.startsWith('+') ? 'text-rose-600' : 'text-blue-600'
                                }`}>
                                  ({deltaText})
                                </span>
                              )}
                            </div>
                          </td>

                          {/* Reference Range */}
                          <td className="py-2.5 px-3 text-slate-600 font-medium">
                            {item.refRange || 'Standard'}
                          </td>

                          {/* Status Badge */}
                          <td className="py-2.5 px-3 text-right">
                            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                              item.status === 'HIGH' ? 'bg-rose-100 text-rose-800' :
                              item.status === 'LOW' ? 'bg-blue-100 text-blue-800' :
                              'bg-emerald-100 text-emerald-800'
                            }`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${
                                item.status === 'HIGH' ? 'bg-rose-600' :
                                item.status === 'LOW' ? 'bg-blue-600' :
                                'bg-emerald-600'
                              }`} />
                              {item.status}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Database className="w-3.5 h-3.5 text-blue-600" />
            <span>Actual records from MSSQL • Zero simulated data</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-bold text-slate-700 shadow-2xs transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export { ParameterTrendChart as ParameterTrendModal };
export default ParameterTrendChart;
