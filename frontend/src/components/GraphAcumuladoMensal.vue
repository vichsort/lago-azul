<script setup>
import { ref, onMounted, watch } from 'vue';
import * as d3 from 'd3';

const props = defineProps({
  data: { 
    type: Array, 
    required: true 
    // Formato esperado: [{ ano: 2023, mes: 1, acumulado_mm: 250.50 }, ...]
  }
});

const svgRef = ref(null);

const drawChart = () => {
  if (!props.data || props.data.length === 0) return;

  // 1. Preparação dos Dados: Converter para objetos com data JS
  const dataset = props.data.map(d => ({
    date: new Date(d.ano, d.mes - 1), // Mês em JS é 0-indexado
    value: d.acumulado_mm
  })).sort((a, b) => a.date - b.date); // Garante a ordem cronológica

  // 2. Setup do SVG e Dimensões
  const svg = d3.select(svgRef.value);
  svg.selectAll('*').remove(); // Limpa o SVG antes de redesenhar

  const margin = { top: 20, right: 30, bottom: 40, left: 60 };
  const width = svg.node().getBoundingClientRect().width - margin.left - margin.right;
  const height = svg.node().getBoundingClientRect().height - margin.top - margin.bottom;

  const chart = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  // 3. Definição das Escalas
  // Eixo X (Temporal)
  const x = d3.scaleTime()
    .domain(d3.extent(dataset, d => d.date)) // Min e Max datas
    .range([0, width]);

  // Eixo Y (Precipitação)
  const y = d3.scaleLinear()
    .domain([0, d3.max(dataset, d => d.value)])
    .range([height, 0]);

  // 4. Desenho dos Eixos
  chart.append('g')
    .attr('class', 'x-axis')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x).ticks(d3.timeYear.every(2)).tickFormat(d3.timeFormat("%Y")));

  chart.append('g')
    .attr('class', 'y-axis')
    .call(d3.axisLeft(y));
  
  // Rótulo do Eixo Y
  chart.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 0 - margin.left + 15)
      .attr("x", 0 - (height / 2))
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .attr("class", "axis-label")
      .text("Precipitação (mm)");

  // 5. Desenho da Linha
  const lineGenerator = d3.line()
    .x(d => x(d.date))
    .y(d => y(d.value));

  chart.append('path')
    .datum(dataset)
    .attr('class', 'line-path')
    .attr('d', lineGenerator);

  // 6. Funcionalidade de Tooltip Interativo
  const tooltip = chart.append('g').style('display', 'none');

  tooltip.append('circle').attr('r', 5).attr('class', 'tooltip-circle');
  tooltip.append('line').attr('class', 'tooltip-line x-line').attr('y1', 0).attr('y2', height);
  tooltip.append('line').attr('class', 'tooltip-line y-line').attr('x1', 0).attr('x2', width);
  const tooltipText = tooltip.append('text').attr('class', 'tooltip-text').attr('x', 15).attr('y', -15);
  
  svg.append('rect')
    .attr('class', 'overlay')
    .attr('width', width)
    .attr('height', height)
    .attr('transform', `translate(${margin.left},${margin.top})`)
    .on('mouseover', () => tooltip.style('display', null))
    .on('mouseout', () => tooltip.style('display', 'none'))
    .on('mousemove', (event) => {
      const [xPos] = d3.pointer(event);
      const date = x.invert(xPos);
      const bisector = d3.bisector(d => d.date).left;
      const index = bisector(dataset, date, 1);
      const d0 = dataset[index - 1];
      const d1 = dataset[index];
      const d = d1 && (date - d0.date > d1.date - date) ? d1 : d0;

      if (d) {
        tooltip.attr('transform', `translate(${x(d.date)},${y(d.value)})`);
        tooltip.select('.x-line').attr('y2', height - y(d.value));
        tooltip.select('.y-line').attr('x2', -x(d.date));
        
        const formatTime = d3.timeFormat("%b %Y"); // Ex: "Jan 2023"
        tooltipText.text(`${formatTime(d.date)}: ${d.value.toFixed(1)} mm`);
      }
    });
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
.chart-container {
  width: 100%;
  height: 100%;
  flex-grow: 1;
}

svg {
  width: 100%;
  height: 100%;
}

:deep(.line-path) {
  fill: none;
  stroke: #0d6efd;
  stroke-width: 2.5px;
}

:deep(.axis-label) {
  font-size: 0.9em;
  fill: #6c757d;
}

:deep(.overlay) {
  fill: none;
  pointer-events: all;
}

:deep(.tooltip-circle) {
  fill: #ff4500;
}

:deep(.tooltip-line) {
  stroke: #aaa;
  stroke-width: 1px;
  stroke-dasharray: 3,3;
}

:deep(.tooltip-text) {
  font-size: 0.9em;
  font-weight: 500;
  fill: #333;
}
</style>