# FastTrack Routing Engine

API de roteirização logística construída com **FastAPI** e **Python 3.12**.  
Calcula rotas de entrega otimizadas usando o **Strategy Pattern**, permitindo trocar o algoritmo de roteamento sem alterar o restante do sistema.

---

## Visão Geral do Desafio

O desafio FastTrack consiste em construir um motor de roteirização capaz de:

- Gerenciar **pacotes** (destinos, pesos, custos de acesso), **veículos** (capacidade máxima) e **hubs** (pontos de despacho no mapa)
- Calcular rotas partindo sempre do **hub principal em (0, 0)**
- Suportar múltiplos critérios de otimização: menor distância, menor custo, consolidação regional
- **Comparar automaticamente** as estratégias e recomendar a melhor rota para cada cenário
- Rejeitar rotas que violem a capacidade do veículo com mensagens de erro claras

---

## Arquitetura da Solução

A aplicação segue **arquitetura em camadas** com separação estrita de responsabilidades:

```
Request → API (FastAPI) → Service → Repository → Domain Model
                              ↕
                         Algorithms (Strategy Pattern)
```

### Camadas

| Camada | Localização | Responsabilidade |
|---|---|---|
| **API** | `app/api/v1/` | Routers FastAPI, validação HTTP, serialização |
| **Schemas** | `app/schemas/` | Contratos Pydantic de entrada e saída |
| **Services** | `app/services/` | Regras de negócio, orquestração |
| **Repositories** | `app/repositories/` | Acesso e persistência de dados |
| **Models** | `app/models/` | Entidades de domínio (dataclasses) |
| **Algorithms** | `app/algorithms/` | Estratégias de roteamento |
| **Core** | `app/core/` | Configurações centralizadas |

---

## Strategy Pattern

O motor de roteamento é construído sobre o padrão **Strategy**, permitindo adicionar novos algoritmos sem modificar código existente (Open/Closed Principle).

### Estrutura

```
RouteStrategy (ABC)
├── calculate_route()        ← template method: valida capacidade → chama _calculate()
└── _calculate()             ← hook implementado por cada estratégia concreta
    ├── ExpressRouteStrategy
    ├── EconomicRouteStrategy
    └── StrategicHubRouteStrategy
```

### Diagrama de colaboração

```
RouteStrategyRegistry
        │
        ├── get("express")       → ExpressRouteStrategy
        ├── get("economic")      → EconomicRouteStrategy
        └── get("strategic_hub") → StrategicHubRouteStrategy
                │
                └── calculate_route(RouteInput)
                        │
                        ├── [base] valida vehicle.max_weight
                        │         └── VehicleCapacityExceededError → HTTP 400
                        │
                        └── [concreto] _calculate(RouteInput) → RouteResult
```

### Contrato

```python
@dataclass
class RouteInput:
    packages: list[Package]
    vehicle:  Vehicle
    origin:   Hub
    available_hubs: list[Hub]

@dataclass
class RouteResult:
    stops:                   list[RouteStop]
    total_distance:          float
    total_cost:              float
    strategy_name:           str
    extra_package_collected: bool
    visited_hub:             Hub | None
```

Para adicionar uma nova estratégia basta criar uma classe que herde de `RouteStrategy` e registrá-la:

```python
class MyCustomStrategy(RouteStrategy):
    @property
    def name(self) -> str:
        return "custom"

    def _calculate(self, route_input: RouteInput) -> RouteResult:
        ...

registry.register(MyCustomStrategy())
```

---

## Algoritmos Utilizados

### Express — Nearest-Neighbor Greedy

**Objetivo:** menor distância total, sem considerar custos.

```
Partida: hub principal (0, 0)
Loop:
  → Seleciona o pacote não visitado mais próximo da posição atual
  → Acumula distância
  → Avança para o pacote selecionado
Retorna: sequência com menor distância total euclidiana
```

- **Complexidade:** O(n²)
- **Ignora:** `access_cost`
- **Garante:** todos os pacotes entregues

---

### Economic — Weighted Nearest-Neighbor

**Objetivo:** menor custo total (distância + custo de acesso).

```
Partida: hub principal (0, 0)
Loop:
  → Calcula score = distância_até_pacote + access_cost
  → Seleciona o pacote com menor score
  → Acumula distância e custo
Retorna: sequência que minimiza custo composto por passo
```

- **Complexidade:** O(n²)
- **Considera:** `access_cost` em cada decisão
- **Permite:** distância maior se o custo de acesso compensar

---

### Strategic Hub — Hub-Cluster

**Objetivo:** consolidação regional via desvio por hub secundário.

```
Partida: hub principal (0, 0)
1. Calcular centroide de todos os pacotes
2. Selecionar hub secundário mais próximo do centroide
3. Identificar pacotes dentro do raio regional (≤ 10 unidades do hub)
4. Respeitar vehicle.max_weight: descartar pacotes mais pesados se necessário
5. Rota: origem → hub → pacotes regionais (nearest-neighbor) → demais pacotes
Retorna: rota com desvio pelo hub + flags extra_package_collected e visited_hub
```

- **Fallback:** se não houver hubs secundários, executa nearest-neighbor simples
- **Considera:** `access_cost` no custo total e `weight` na capacidade do cluster

---

### Distância Euclidiana

Todas as estratégias utilizam a fórmula:

```
d(A, B) = √((x₂ - x₁)² + (y₂ - y₁)²)
```

Implementada em `DistanceCalculator` com o protocolo `Locatable`, compatível com `Hub`, `Package` e `Point`.

---

## Endpoints

Base URL: `http://localhost:8000/api/v1`

### Packages

| Método | Rota | Descrição | Status |
|---|---|---|---|
| `GET` | `/packages` | Lista todos os pacotes | 200 |
| `GET` | `/packages/{id}` | Busca pacote por ID | 200 / 404 |
| `POST` | `/packages` | Cria novo pacote | 201 / 422 |
| `PATCH` | `/packages/{id}` | Atualiza parcialmente | 200 / 404 |
| `DELETE` | `/packages/{id}` | Remove pacote | 204 / 404 |

### Vehicles

| Método | Rota | Descrição | Status |
|---|---|---|---|
| `GET` | `/vehicles` | Lista todos os veículos | 200 |
| `GET` | `/vehicles/{id}` | Busca veículo por ID | 200 / 404 |
| `POST` | `/vehicles` | Registra novo veículo | 201 / 409 |
| `PATCH` | `/vehicles/{id}` | Atualiza parcialmente | 200 / 404 / 409 |
| `DELETE` | `/vehicles/{id}` | Remove veículo | 204 / 404 |

### Hubs

| Método | Rota | Descrição | Status |
|---|---|---|---|
| `GET` | `/hubs` | Lista todos os hubs | 200 |
| `GET` | `/hubs/main` | Retorna o hub principal | 200 |
| `GET` | `/hubs/{id}` | Busca hub por ID | 200 / 404 |
| `POST` | `/hubs` | Cria hub secundário | 201 / 409 |
| `PATCH` | `/hubs/{id}` | Atualiza hub secundário | 200 / 403 / 404 / 409 |
| `DELETE` | `/hubs/{id}` | Remove hub secundário | 204 / 403 / 404 |

> O hub principal `(0, 0)` não pode ser modificado nem deletado (`403 Forbidden`).

### Routes

| Método | Rota | Descrição | Status |
|---|---|---|---|
| `POST` | `/routes/calculate` | Calcula rota com uma estratégia | 200 / 400 / 404 / 422 |
| `POST` | `/routes/calculate/all` | Executa as 3 estratégias em paralelo e compara | 200 / 400 / 404 |

#### Exemplo — `POST /routes/calculate/all`

**Request:**
```json
{
  "vehicle_id": "b7e23ec2-9428-4f3e-9e49-a9e9d13bce40",
  "package_ids": [
    "a3bb189e-8bf9-3888-9912-ace4e6543002",
    "d290f1ee-6c54-4b01-90e6-d701748f0851"
  ]
}
```

**Response `200`:**
```json
{
  "express_route":  { "route_type": "express",       "total_distance": 10.0, "total_cost": 0.0,  "delivery_order": [...] },
  "economic_route": { "route_type": "economic",      "total_distance": 14.0, "total_cost": 5.0,  "delivery_order": [...] },
  "strategic_route":{ "route_type": "strategic_hub", "total_distance": 12.0, "total_cost": 5.0,  "delivery_order": [...], "visited_hub": {...} },
  "comparison": {
    "shortest_route":            { "strategy": "express",  "total_distance": 10.0 },
    "cheapest_route":            { "strategy": "express",  "total_cost": 0.0 },
    "highest_utilization_route": { "strategy": "economic", "stops": 2 },
    "distance_saved": 4.0,
    "cost_saved": 5.0,
    "recommended": {
      "strategy": "express",
      "reason": "Recommended because it offers the shortest total distance and lowest total cost."
    }
  }
}
```

---

## Swagger

A API disponibiliza documentação interativa em dois formatos:

| Interface | URL |
|---|---|
| Swagger UI | [http://localhost:8000/docs](http://localhost:8000/docs) |
| ReDoc | [http://localhost:8000/redoc](http://localhost:8000/redoc) |
| OpenAPI JSON | [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) |

Todos os endpoints possuem:
- `summary` e `description` detalhados
- Exemplos de request body no Swagger UI
- Tabela de códigos de resposta com descrições
- Campos com `description` e `examples` no schema

---

## Testes

Os testes unitários cobrem todas as camadas de lógica sem dependência de HTTP.

### Executar

```bash
# Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt

# Executar todos os testes
pytest tests/ -v

# Executar com sumário de cobertura por módulo
pytest tests/ -v --tb=short
```

### Suítes

| Arquivo | O que testa | Testes |
|---|---|---|
| `test_distance_calculator.py` | `DistanceCalculator` — fórmula euclidiana, casos extremos, protocolo `Locatable` | 18 |
| `test_express_strategy.py` | `ExpressRouteStrategy` — ordem nearest-neighbor, distância, indiferença ao custo | 11 |
| `test_economic_strategy.py` | `EconomicRouteStrategy` — score composto, preferência por custo, divergência vs express | 12 |
| `test_strategic_hub_strategy.py` | `StrategicHubRouteStrategy` — desvio por hub, cluster regional, limite de carga, fallback | 16 |
| `test_capacity_validation.py` | `VehicleCapacityExceededError` — mensagem, atributos, validação nas 3 estratégias | 19 |
| `test_route_comparison.py` | `RouteComparisonService` — shortest, cheapest, utilization, savings, recommendation | 15 |
| **Total** | | **91** |

---

## Docker

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) ≥ 24
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2.20

### Subir em produção

```bash
docker compose up -d
```

A API estará disponível em `http://localhost:8000`.

### Outros comandos

```bash
# Rebuild após mudança de código
docker compose up -d --build

# Verificar status e saúde do container
docker compose ps
docker inspect --format='{{.State.Health.Status}}' fasttrack-api

# Logs em tempo real
docker compose logs -f api

# Encerrar
docker compose down
```

### Configuração via variáveis de ambiente

Copie `.env.example` para `.env` e ajuste os valores:

```bash
cp .env.example .env
```

| Variável | Padrão | Descrição |
|---|---|---|
| `HOST_PORT` | `8000` | Porta exposta no host |
| `WORKERS` | `2` | Número de workers Uvicorn |
| `LOG_LEVEL` | `info` | Nível de log (`debug`, `info`, `warning`, `error`) |
| `DEBUG` | `false` | Modo debug da aplicação |

### Dockerfile — estratégia multi-stage

```
Stage 1: builder   → instala dependências em /venv isolado
Stage 2: runtime   → copia apenas /venv + código-fonte
                   → usuário não-root (appuser)
                   → sem pip, sem build tools na imagem final
```

---

## Como Executar Localmente

### Pré-requisitos

- Python 3.12
- pip

### Passo a passo

```bash
# 1. Clonar o repositório
git clone https://github.com/your-org/fasttrack-routing-engine.git
cd fasttrack-routing-engine

# 2. Instalar dependências
pip install -r requirements-dev.txt

# 3. (Opcional) Configurar variáveis de ambiente
cp .env.example .env

# 4. Iniciar a API
uvicorn main:app --reload

# 5. Acessar a documentação
# http://localhost:8000/docs
```

### Verificar saúde da API

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### Exemplo rápido de uso

```bash
# 1. Registrar veículo
curl -s -X POST http://localhost:8000/api/v1/vehicles \
  -H "Content-Type: application/json" \
  -d '{"plate": "ABC-1234", "max_weight": 100}' | python -m json.tool

# 2. Registrar pacotes
curl -s -X POST http://localhost:8000/api/v1/packages \
  -H "Content-Type: application/json" \
  -d '{"recipient_name": "Maria Silva", "destination_x": 3, "destination_y": 4, "weight": 5, "access_cost": 10}' | python -m json.tool

# 3. Calcular todas as rotas (use os IDs retornados acima)
curl -s -X POST http://localhost:8000/api/v1/routes/calculate/all \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id": "<VEHICLE_ID>", "package_ids": ["<PACKAGE_ID>"]}' | python -m json.tool
```

---

## Estrutura do Projeto

```
fasttrack-routing-engine/
│
├── app/
│   ├── algorithms/                  # Strategy Pattern — motor de roteamento
│   │   ├── base.py                  # RouteStrategy (ABC) + VehicleCapacityExceededError
│   │   ├── models.py                # RouteInput · RouteStop · RouteResult
│   │   ├── express.py               # ExpressRouteStrategy (nearest-neighbor)
│   │   ├── economic.py              # EconomicRouteStrategy (weighted nearest-neighbor)
│   │   ├── strategic_hub.py         # StrategicHubRouteStrategy (hub-cluster)
│   │   └── registry.py              # RouteStrategyRegistry
│   │
│   ├── api/v1/                      # Routers FastAPI
│   │   ├── packages.py
│   │   ├── vehicles.py
│   │   ├── hubs.py
│   │   └── routes_calc.py
│   │
│   ├── core/
│   │   └── config.py                # Settings via pydantic-settings + .env
│   │
│   ├── models/                      # Entidades de domínio (dataclasses)
│   │   ├── package.py
│   │   ├── vehicle.py
│   │   └── hub.py
│   │
│   ├── repositories/                # Persistência in-memory
│   │   ├── package_repository.py
│   │   ├── vehicle_repository.py
│   │   └── hub_repository.py        # Seed automático do hub principal
│   │
│   ├── schemas/                     # Schemas Pydantic (request / response)
│   │   ├── package.py
│   │   ├── vehicle.py
│   │   ├── hub.py
│   │   └── route.py                 # RouteRequest · RouteResponse · AllRoutesResponse · RouteComparison
│   │
│   └── services/
│       ├── distance_calculator.py   # DistanceCalculator + Locatable Protocol + Point
│       ├── route_comparison.py      # RouteComparisonService
│       ├── package_service.py
│       ├── vehicle_service.py
│       └── hub_service.py
│
├── tests/
│   ├── test_distance_calculator.py
│   ├── test_express_strategy.py
│   ├── test_economic_strategy.py
│   ├── test_strategic_hub_strategy.py
│   ├── test_capacity_validation.py
│   └── test_route_comparison.py
│
├── main.py                          # FastAPI app + metadados OpenAPI
├── Dockerfile                       # Multi-stage build (builder + runtime)
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── requirements.txt                 # Dependências de produção
└── requirements-dev.txt             # + pytest
```

---

## Stack Técnica

| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.12 | Linguagem principal |
| FastAPI | 0.115.0 | Framework web e OpenAPI |
| Uvicorn | 0.30.6 | Servidor ASGI |
| Pydantic | 2.9.2 | Validação de dados e schemas |
| pydantic-settings | 2.5.2 | Configuração via variáveis de ambiente |
| pytest | 8.3.3 | Testes unitários |
| Docker | ≥ 24 | Containerização |

---

## Princípios SOLID Aplicados

| Princípio | Aplicação |
|---|---|
| **SRP** | Cada classe tem uma única responsabilidade: `DistanceCalculator` só calcula distâncias, `RouteComparisonService` só compara rotas |
| **OCP** | Novas estratégias são adicionadas via `registry.register()` sem alterar código existente |
| **LSP** | `ExpressRouteStrategy`, `EconomicRouteStrategy` e `StrategicHubRouteStrategy` são substituíveis por `RouteStrategy` em qualquer contexto |
| **ISP** | `Locatable` Protocol expõe apenas `x` e `y` — `Hub` e `Package` satisfazem o contrato sem herança |
| **DIP** | O endpoint depende de `RouteStrategy` (abstração), nunca das implementações concretas |
