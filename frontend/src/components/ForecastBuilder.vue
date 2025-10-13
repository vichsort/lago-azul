<script setup>
import { ref, onMounted } from 'vue';

// --- Estado do Componente ---
const isLoadingCities = ref(true);
const isGeneratingForecast = ref(false);
const error = ref(null);
const availableCities = ref([]);
const selectedCity = ref('');
const forecastResult = ref(null); // Para armazenar a resposta da API

const API_BASE_URL = 'http://127.0.0.1:5000/api/v1';

// --- Funções ---

// Busca a lista de cidades para popular o dropdown
async function fetchCities() {
    isLoadingCities.value = true;
    try {
        const response = await fetch(`${API_BASE_URL}/cities`);
        if (!response.ok) throw new Error('Não foi possível carregar a lista de cidades.');
        availableCities.value = await response.json();
    } catch (err) {
        error.value = err.message;
    } finally {
        isLoadingCities.value = false;
    }
}

// Função principal, acionada pelo botão
async function handleGenerateForecast() {
    if (!selectedCity.value) return;

    isGeneratingForecast.value = true;
    error.value = null;
    forecastResult.value = null;

    try {
        // Faz a chamada POST para acionar a geração da previsão
        const response = await fetch(`${API_BASE_URL}/forecast/by-city/${selectedCity.value}`, {
            method: 'POST',
        });

        const result = await response.json();

        if (!response.ok) {
            // Se a API retornar um erro (ex: 400 por falta de dados), lança o erro
            throw new Error(result.message || 'Ocorreu um erro ao gerar a previsão.');
        }

        // Armazena a resposta de sucesso
        forecastResult.value = result;

    } catch (err) {
        console.error('Erro na geração da previsão:', err);
        error.value = err.message;
    } finally {
        isGeneratingForecast.value = false;
    }
}

// Busca as cidades quando o componente é montado
onMounted(fetchCities);
</script>

<template>
    <div class="builder-container">
        <div class="builder-wrapper">
            <h1 class="builder-title">Gerador de Previsão</h1>
            <p class="lead text-center mb-4">
                Selecione uma cidade e clique em "Gerar Previsão" para executar o modelo estatístico.
            </p>

            <div class="row justify-content-center mb-3">
                <div class="col-md-8">
                    <div v-if="isLoadingCities" class="text-center">
                        <div class="spinner-border spinner-border-sm" role="status"></div>
                        <span> Carregando cidades...</span>
                    </div>
                    <div v-else class="input-group input-group-lg">
                        <select class="form-select" v-model="selectedCity" :disabled="isGeneratingForecast">
                            <option value="" disabled>-- Selecione uma cidade --</option>
                            <option v-for="city in availableCities" :key="city" :value="city">
                                {{ city }}
                            </option>
                        </select>
                        <button class="btn btn-primary" @click="handleGenerateForecast"
                            :disabled="!selectedCity || isGeneratingForecast">
                            Gerar Previsão
                        </button>
                    </div>
                </div>
            </div>

            <div class="result-area">
                <div v-if="isGeneratingForecast" class="status-card text-center">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-3">
                        <strong>Gerando previsão para {{ selectedCity }}...</strong><br>
                        Este processo pode levar até um minuto. O modelo `auto_arima` está trabalhando.
                    </p>
                </div>

                <div v-else-if="error" class="alert alert-danger">
                    <strong>Erro:</strong> {{ error }}
                </div>

                <div v-else-if="forecastResult" class="alert alert-success">
                    <strong>Sucesso!</strong> {{ forecastResult.message }}
                    <hr>
                    <p class="mb-1">Os dados foram salvos no cache do servidor. Agora você pode visualizá-los no
                        dashboard principal.</p>
                    <router-link to="/" class="alert-link">Voltar para o Dashboard</router-link>
                </div>

                <div v-else class="status-card text-center">
                    <p class="text-muted">Aguardando seleção para iniciar a análise.</p>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.builder-container {
    padding: 3rem;
    background-color: #f8f9fa;
    min-height: 80vh;
    display: flex;
    align-items: flex-start;
    justify-content: center;
}

.builder-wrapper {
    width: 100%;
    max-width: 800px;
}

.builder-title {
    text-align: center;
    margin-bottom: 1rem;
}

.result-area {
    margin-top: 2rem;
    min-height: 150px;
}

.status-card {
    padding: 3rem;
    background-color: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
</style>