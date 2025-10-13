<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import GraficoAcumuladoAnual from './GraphAcumuladoAnual.vue';
import GraficoAcumuladoMensal from './GraphAcumuladoMensal.vue';
import GraficoPrevisao from './GraphPrevisao.vue';

const isLoading = ref(true);
const error = ref(null);
const availableCities = ref([]);
const selectedCity = ref('');

// Estrutura para armazenar todos os dados da cidade selecionada
const cityData = ref({
    yearly: [],
    monthly: [],
    extremes: null,
    forecast: null
});

const API_BASE_URL = 'http://127.0.0.1:5000/api/v1';

// --- Funções de API ---
async function fetchCities() {
    const response = await fetch(`${API_BASE_URL}/cities`);
    if (!response.ok) throw new Error('Não foi possível carregar a lista de cidades.');
    availableCities.value = await response.json();
    if (availableCities.value.length > 0) {
        selectedCity.value = availableCities.value[0]; // Seleciona a primeira cidade por padrão
    }
}

async function fetchAllDataForCity(city) {
    if (!city) return;
    isLoading.value = true;
    error.value = null;
    try {
        const endpoints = [
            `/stats/accumulation/yearly/by-city/${city}`,
            `/stats/accumulation/monthly/by-city/${city}`,
            `/stats/extremes/by-city/${city}`,
            `/forecast/by-city/${city}`
        ];
        const requests = endpoints.map(endpoint => fetch(API_BASE_URL + endpoint));
        const responses = await Promise.all(requests);

        // Verifica se todas as respostas foram bem-sucedidas
        for (const res of responses) {
            if (!res.ok) {
                // Se a previsão falhar (404), não tratamos como um erro fatal
                if (res.status === 404 && res.url.includes('/forecast/')) {
                    continue;
                }
                throw new Error(`Falha ao buscar um dos recursos para a cidade: ${city}`);
            }
        }

        const [yearlyRes, monthlyRes, extremesRes, forecastRes] = responses;

        cityData.value = {
            yearly: await yearlyRes.json(),
            monthly: await monthlyRes.json(),
            extremes: await extremesRes.json(),
            // Trata o caso onde a previsão não existe (404)
            forecast: forecastRes.ok ? await forecastRes.json() : null
        };

    } catch (err) {
        console.error(`Erro ao buscar dados para ${city}:`, err);
        error.value = err.message;
    } finally {
        isLoading.value = false;
    }
}

// Cards de insight
const kpiRainiestDay = computed(() => {
    return cityData.value.extremes?.dia_mais_chuvoso || { data: 'N/D', precipitacao_mm: 'N/D' };
});

const kpiYearlyStats = computed(() => {
    if (!cityData.value.yearly || cityData.value.yearly.length === 0) {
        return { rainiestYear: 'N/D', avgAnnual: 'N/D' };
    }
    const rainiest = cityData.value.yearly.reduce((max, year) => year.acumulado_mm > max.acumulado_mm ? year : max);
    const total = cityData.value.yearly.reduce((sum, year) => sum + year.acumulado_mm, 0);
    const avg = total / cityData.value.yearly.length;
    return {
        rainiestYear: `${rainiest.ano} (${rainiest.acumulado_mm.toFixed(0)} mm)`,
        avgAnnual: `${avg.toFixed(0)} mm`
    };
});


// Hooks 
onMounted(async () => {
    await fetchCities();
});

// Observa mudanças na cidade selecionada e busca novos dados
watch(selectedCity, (newCity) => {
    fetchAllDataForCity(newCity);
});

</script>

<template>
    <div class="dashboard-container">
        <div v-if="isLoading && !cityData.extremes" class="loading-state">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-3">Carregando dados...</p>
        </div>

        <div v-else-if="error" class="alert alert-danger">
            <h4>😕 Ops! Algo deu errado.</h4>
            <p>{{ error }}</p>
        </div>

        <div v-else class="dashboard-wrapper">
            <h1 class="dashboard-title mb-4">Dashboard</h1>

            <div class="row mb-4">
                <div class="col-md-6 offset-md-3">
                    <label for="city-select" class="form-label">Selecione uma Cidade</label>
                    <select id="city-select" class="form-select form-select-lg" v-model="selectedCity">
                        <option v-for="city in availableCities" :key="city" :value="city">
                            {{ city }}
                        </option>
                    </select>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="chart-title">Precipitação Total Mensal (Histórico)</h5>
                        </div>
                        <GraficoAcumuladoMensal v-if="cityData.monthly.length > 0" :data="cityData.monthly" />
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-md-4 px-2">
                    <div class="card text-center kpi-card">
                        <div class="card-body">
                            <h5 class="card-title">Dia Mais Chuvoso</h5>
                            <p class="kpi-value-small">{{ new Date(kpiRainiestDay.data).toLocaleDateString() }}</p>
                            <p class="kpi-value">{{ kpiRainiestDay.precipitacao_mm }} mm</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 px-2">
                    <div class="card text-center kpi-card">
                        <div class="card-body">
                            <h5 class="card-title">Ano Mais Chuvoso</h5>
                            <p class="kpi-value">{{ kpiYearlyStats.rainiestYear }}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 px-2">
                    <div class="card text-center kpi-card">
                        <div class="card-body">
                            <h5 class="card-title">Média Anual de Chuva</h5>
                            <p class="kpi-value">{{ kpiYearlyStats.avgAnnual }}</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="chart-title">Precipitação Total Mensal (Histórico)</h5>
                        </div>
                        <GraficoAcumuladoMensal v-if="cityData.monthly.length > 0" :data="cityData.monthly" />
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-6 mb-3 mb-md-0 px-2">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="chart-title">Precipitação Total Anual (Comparativo)</h5>
                        </div>
                        <GraficoAcumuladoAnual v-if="cityData.yearly.length > 0" :data="cityData.yearly" />
                    </div>
                </div>
                <div class="col-md-6 px-2">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="chart-title">Previsão para os Próximos 12 Meses</h5>
                        </div>
                        <GraficoPrevisao v-if="cityData.forecast" :historico="cityData.monthly"
                            :previsao="cityData.forecast" />
                        <div v-else class="text-center p-5">
                            <p>Previsão não disponível para esta cidade. É necessário gerá-la via API.</p>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </div>
</template>

<style scoped>
.dashboard-container {
    padding: 2rem;
    background-color: #f8f9fa;
}

.dashboard-wrapper {
    width: 100%;
    max-width: 1200px;
    margin: auto;
}

.dashboard-title {
    color: #333;
    text-align: center;
}

.loading-state {
    text-align: center;
    padding: 4rem;
}

.kpi-card {
    border: none;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    min-height: 160px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.kpi-card .card-title {
    font-size: 1.1rem;
    color: #6c757d;
    font-weight: 500;
}

.kpi-card .kpi-value {
    font-size: 2.2rem;
    font-weight: 700;
    color: #0d6efd;
    margin-top: 0.5rem;
}

.kpi-card .kpi-value-small {
    font-size: 1rem;
}

.card {
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    display: flex;
    flex-direction: column;
}

.chart-title {
    font-weight: 600;
    text-align: center;
}
</style>