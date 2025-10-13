<script setup>
import { ref, onMounted, watch } from 'vue';
import * as d3 from 'd3';

const props = defineProps({
  // A prop 'historico' ainda é recebida, mas não será usada para desenhar o gráfico.
  historico: { type: Array, required: true },
  previsao: { type: Object, required: true }
});

const svgRef = ref(null);

const drawChart = () => {
  // A verificação agora foca apenas nos dados da previsão
  if (!props.previsao || !props.previsao.forecast) return;

  // 1. Preparação dos Dados (usamos APENAS a previsão)
  const previsaoData = props.previsao.forecast.map(d => ({
    date: new Date(d.date),
    value: d.predicted_mm,
    lower: d.conf_int_lower,
    upper: d.conf_int_upper,
  }));
  
  // 2. Setup do SVG
  const svg = d3.select(svgRef.value);
  svg.selectAll('*').remove();

  const margin = { top: 20, right: 30, bottom: 40, left: 60 };
  const width = svg.node().getBoundingClientRect().width - margin.left - margin.right;
  const height = svg.node().getBoundingClientRect().height - margin.top - margin.bottom;

  const chart = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

  // <<< MUDANÇA PRINCIPAL: DOMÍNIO DAS ESCALAS BASEADO APENAS NA PREVISÃO >>>
  // 3. Escalas
  // Domínio X é definido apenas pelo intervalo de datas da previsão
  const x = d3.scaleTime()
    .domain(d3.extent(previsaoData, d => d.date))
    .range([0, width]);

  // Domínio Y é definido pelo valor máximo do intervalo de confiança da previsão
  const y = d3.scaleLinear()
    .domain([0, d3.max(previsaoData, d => d.upper) * 1.05]) // Margem de 5% no topo
    .range([height, 0]);

  // 4. Eixos
  // Formato do eixo X agora mostra Mês/Ano
  chart.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x).ticks(d3.timeMonth.every(2)).tickFormat(d3.timeFormat("%b/%y")));
    
  chart.append('g').call(d3.axisLeft(y));
  
  chart.append("text").attr("transform", "rotate(-90)").attr("y", -margin.left + 15).attr("x", -(height / 2))
      .attr("dy", "1em").style("text-anchor", "middle").attr("class", "axis-label").text("Precipitação (mm)");

  // <<< MUDANÇA PRINCIPAL: REMOÇÃO DA LINHA HISTÓRICA >>>
  // 5. Desenho das Áreas e Linhas (apenas previsão)
  const areaGenerator = d3.area().x(d => x(d.date)).y0(d => y(d.lower)).y1(d => y(d.upper));
  chart.append('path').datum(previsaoData).attr('class', 'confidence-area').attr('d', areaGenerator);

  const lineGenerator = d3.line().x(d => x(d.date)).y(d => y(d.value));
  // A linha histórica azul NÃO é mais desenhada
  chart.append('path').datum(previsaoData).attr('class', 'line-forecast').attr('d', lineGenerator);

  // 6. Lógica do Tooltip (sem alterações, já estava focada na previsão)
  const tooltip = chart.append('g').style('display', 'none');
  const tooltipLine = tooltip.append('line').attr('class', 'tooltip-line').attr('y1', 0).attr('y2', height);
  const tooltipCircle = tooltip.append('circle').attr('r', 5).attr('class', 'tooltip-circle-forecast');
  const tooltipText = tooltip.append('text').attr('class', 'tooltip-text').attr('dy', '-1em');

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
        const index = bisector(previsaoData, date, 1);
        const d0 = previsaoData[index - 1];
        const d1 = previsaoData[index];
        if (!d0 && !d1) return;
        const d = d1 && (date - d0.date > d1.date - date) ? d1 : d0;
        
        if (d) {
          const dataPointX = x(d.date);
          tooltipLine.attr('transform', `translate(${dataPointX},0)`);
          tooltipCircle.attr('transform', `translate(${dataPointX},${y(d.value)})`);
          
          const textContent = `Previsão: ${d.value.toFixed(1)} mm (${d3.timeFormat("%b %Y")(d.date)})`;
          tooltipText.text(textContent);
          
          if (dataPointX > width / 2) {
            tooltipText.attr('text-anchor', 'end').attr('transform', `translate(${dataPointX - 15},10)`);
          } else {
            tooltipText.attr('text-anchor', 'start').attr('transform', `translate(${dataPointX + 15},10)`);
          }
        }
    });
};

onMounted(drawChart);
watch(() => [props.historico, props.previsao], drawChart, { deep: true });
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

:deep(.line-historical) {
  fill: none;
  stroke: #0d6efd;
  stroke-width: 2.5px;
}

:deep(.line-forecast) {
  fill: none;
  stroke: #dc3545;
  stroke-width: 2.5px;
  stroke-dasharray: 6, 6;
}

:deep(.confidence-area) {
  fill: #f8d7da;
  opacity: 0.6;
}

:deep(.axis-label) {
  font-size: 0.9em;
  fill: #6c757d;
}

/* --- ESTILOS DO TOOLTIP --- */
:deep(.overlay) {
  fill: none;
  pointer-events: all;
}

:deep(.tooltip-line) {
  stroke: #999;
  stroke-width: 1px;
  stroke-dasharray: 2,2;
}

:deep(.tooltip-circle-historical) {
  fill: #0d6efd;
}

:deep(.tooltip-circle-forecast) {
  fill: #dc3545;
}

:deep(.tooltip-text) {
  font-size: 0.9em;
  font-weight: bold;
  fill: #333;
}
</style>