/**
 * Layout Engine v4
 * 自动计算图件节点坐标 — 分层布局算法
 *
 * 支持：
 *   - system_architecture  → 垂直分层（上→下）
 *   - network_topology     → 垂直分层（网络设备层级）
 *   - data_flow            → 垂直流程布局
 *   - deployment_structure → 水平分区布局（服务器区域）
 *
 * 输入：chart_data.json（AI 生成，无坐标）
 * 输出：{ pos, layerRects } （坐标信息，供渲染引擎使用）
 *
 * AI 禁止直接生成坐标。坐标由本模块计算。
 */

;(function(root, factory) {
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = factory()          // Node.js / CommonJS
  } else {
    root.LayoutEngine = factory()       // 浏览器全局
  }
}(typeof self !== 'undefined' ? self : this, function() {

  // ── 画布常量 ──────────────────────────────────────────────────
  const W  = 1920
  const H  = 1080
  const TITLE_H      = 90    // 标题栏高度
  const FOOTER_H     = 45    // 底栏高度
  const PAD_X        = 50    // 左右边距
  const PAD_Y        = 14    // 上下内边距
  const NODE_W       = 180   // 节点宽
  const NODE_H       = 88    // 节点高
  const GAP_X        = 46    // 节点水平间距
  const GAP_Y        = 30    // 节点垂直间距（水平布局）
  const LAYER_STRIP  = 118   // 层标签条宽度（垂直布局左侧）
  const PILLAR_W     = 44    // 三体系纵栏宽度（px）
  const PILLAR_GAP   = 8     // 三体系纵栏间距（px）

  // ── 层颜色调色板（政务/公安投标风格） ──────────────────────────
  const LAYER_PAL = [
    { bg:'#DBEAFE', border:'#1d4ed8', text:'#1e40af', strip:'#1d4ed8', stripText:'#fff' },
    { bg:'#DCFCE7', border:'#15803d', text:'#14532d', strip:'#15803d', stripText:'#fff' },
    { bg:'#FEF9C3', border:'#a16207', text:'#854d0e', strip:'#ca8a04', stripText:'#fff' },
    { bg:'#F3E8FF', border:'#7e22ce', text:'#581c87', strip:'#7e22ce', stripText:'#fff' },
    { bg:'#FCE7F3', border:'#be185d', text:'#9d174d', strip:'#be185d', stripText:'#fff' },
  ]

  // ── 公共工具 ──────────────────────────────────────────────────
  function groupByLayer(nodes, layers) {
    const map = {}
    layers.forEach(l => (map[l] = []))
    nodes.forEach(n => {
      if (n.layer && map[n.layer] !== undefined) {
        map[n.layer].push(n)
      }
    })
    return map
  }

  // ── 垂直分层布局 ──────────────────────────────────────────────
  // 适用于：system_architecture / network_topology / data_flow
  function computeVertical(chart) {
    const layers  = chart.layers  || []
    const nodes   = chart.nodes   || []
    const pillars = chart.pillars || []
    const byLayer = groupByLayer(nodes, layers)
    const pillarsW = pillars.length * (PILLAR_W + PILLAR_GAP)

    const usableH = H - TITLE_H - FOOTER_H - PAD_Y * 2
    const layerH  = layers.length > 0 ? usableH / layers.length : usableH

    const pos        = {}
    const layerRects = []

    layers.forEach((name, li) => {
      const lNodes = byLayer[name] || []
      const count  = lNodes.length
      const pal    = LAYER_PAL[li % LAYER_PAL.length]

      const layerY = TITLE_H + PAD_Y + li * layerH

      layerRects.push({
        name, x: PAD_X, y: layerY,
        w: W - PAD_X * 2 - pillarsW, h: layerH - 24,
        pal, li
      })

      if (count === 0) return

      const mainW = W - PAD_X * 2 - LAYER_STRIP - pillarsW
      const totalNodesW = count * NODE_W + (count - 1) * GAP_X
      const startX = PAD_X + LAYER_STRIP + Math.max(0, (mainW - totalNodesW) / 2)
      const innerPadV = Math.max(16, layerH * 0.10)
      const nodeY     = layerY + innerPadV + (layerH - innerPadV * 2 - NODE_H) * 0.38

      lNodes.forEach((n, ni) => {
        pos[n.id] = {
          x: startX + ni * (NODE_W + GAP_X),
          y: nodeY,
          w: NODE_W, h: NODE_H
        }
      })
    })

    return { pos, layerRects, layoutType: 'vertical' }
  }

  // ── 水平分区布局 ──────────────────────────────────────────────
  // 适用于：deployment_structure（每层 = 一台服务器/区域）
  function computeHorizontal(chart) {
    const layers = chart.layers || []
    const nodes  = chart.nodes  || []
    const byLayer = groupByLayer(nodes, layers)

    const usableW  = W - PAD_X * 2
    const usableH  = H - TITLE_H - FOOTER_H - PAD_Y * 2 - 40
    const zoneW    = layers.length > 0 ? usableW / layers.length : usableW

    const pos        = {}
    const layerRects = []

    layers.forEach((name, li) => {
      const lNodes = byLayer[name] || []
      const pal    = LAYER_PAL[li % LAYER_PAL.length]

      const zoneX = PAD_X + li * zoneW
      const zoneY = TITLE_H + PAD_Y + 40

      layerRects.push({
        name,
        x: zoneX + 5, y: zoneY,
        w: zoneW - 10, h: usableH,
        pal, li, horizontal: true
      })

      const count = lNodes.length
      if (count === 0) return

      const totalH = count * NODE_H + (count - 1) * GAP_Y
      const startY = zoneY + 40 + (usableH - 40 - totalH) / 2
      const nodeX  = zoneX + (zoneW - NODE_W) / 2

      lNodes.forEach((n, ni) => {
        pos[n.id] = {
          x: nodeX,
          y: startY + ni * (NODE_H + GAP_Y),
          w: NODE_W, h: NODE_H
        }
      })
    })

    return { pos, layerRects, layoutType: 'horizontal' }
  }

  // ── 自动网格布局 ──────────────────────────────────────────────
  // 无 layers 字段时的 fallback
  function computeAuto(chart) {
    const nodes = chart.nodes || []
    const count = nodes.length
    const cols  = Math.ceil(Math.sqrt(count * 1.5))
    const rows  = Math.ceil(count / cols)

    const usableW = W - PAD_X * 2
    const usableH = H - TITLE_H - FOOTER_H - PAD_Y * 2
    const cellW   = usableW / Math.max(cols, 1)
    const cellH   = usableH / Math.max(rows, 1)

    const pos = {}
    nodes.forEach((n, i) => {
      const col = i % cols
      const row = Math.floor(i / cols)
      pos[n.id] = {
        x: PAD_X + col * cellW + (cellW - NODE_W) / 2,
        y: TITLE_H + PAD_Y + row * cellH + (cellH - NODE_H) / 2,
        w: NODE_W, h: NODE_H
      }
    })

    return { pos, layerRects: [], layoutType: 'auto' }
  }

  // ── 主入口 ────────────────────────────────────────────────────
  return {
    LAYER_PAL,
    NODE_W, NODE_H, GAP_X, GAP_Y, LAYER_STRIP, PILLAR_W, PILLAR_GAP,
    W, H, TITLE_H, FOOTER_H, PAD_X, PAD_Y,

    /**
     * compute(chart)
     * @param  {Object} chart  chart_data.json 对象
     * @return {Object}        { pos, layerRects, layoutType }
     *   pos        — { [nodeId]: {x, y, w, h} }
     *   layerRects — 层背景矩形信息数组
     *   layoutType — 'vertical' | 'horizontal' | 'auto'
     */
    compute(chart) {
      const type   = chart.chart_type || 'system_architecture'
      const layers = chart.layers || []

      if (type === 'deployment_structure') {
        return computeHorizontal(chart)
      }
      if (layers.length === 0) {
        return computeAuto(chart)
      }
      return computeVertical(chart)
    }
  }
}))
