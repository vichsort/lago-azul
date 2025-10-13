<script setup>
import { ref, onMounted, watch } from 'vue';
import * as d3 from 'd3';

const props = defineProps({
  data: { type: Array, required: true }
});

const svgRef = ref(null);

const drawChart = () => {
  if (!props.data || props.data.length === 0) return;

  const svg = d3.select(svgRef.value);
  svg.selectAll('*').remove(); // Limpa o SVG anterior

  const margin = { top: 20, right: 20, bottom: 40, left: 60 };
  const width = svg.node().getBoundingClientRect().width - margin.left - margin.right;
  const height = svg.node().getBoundingClientRect().height - margin.top - margin.bottom;

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

  // Eixo X (Anos)
  const x = d3.scaleBand()
    .range([0, width])
    .domain(props.data.map(d => d.ano))
    .padding(0.2);
  g.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x));

  // Eixo Y (Precipitação em mm)
  const y = d3.scaleLinear()
    .domain([0, d3.max(props.data, d => d.acumulado_mm)])
    .range([height, 0]);
  g.append('g').call(d3.axisLeft(y));

  // Barras
  g.selectAll('rect')
    .data(props.data)
    .join('rect')
    .attr('x', d => x(d.ano))
    .attr('y', d => y(d.acumulado_mm))
    .attr('width', x.bandwidth())
    .attr('height', d => height - y(d.acumulado_mm))
    .attr('fill', '#0d6efd');
};

onMounted(drawChart);
watch(() => props.data, drawChart, { deep: true });
</script>

<template>
  <div class="chart-container">
    <svg ref="svgRef"></svg>
  </div>
</template>

<style scoped>
.chart-container { width: 100%; height: 100%; flex-grow: 1; }
svg { width: 100%; height: 100%; }
</style>