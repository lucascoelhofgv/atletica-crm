# Planilhas do Drive — o que serve de entrada para o CRM

Levantamento feito no Google Drive do Lucas (conta `lucascoelhoxtl@gmail.com`)
em **09/09/2026**. Abaixo, as planilhas relevantes para a operação da Atlética,
o que cada uma contém e para qual módulo do CRM ela pode virar **entrada de
dados** (import) ou **referência de modelagem**.

> Legenda de status: 🟢 import direto viável · 🟡 import com limpeza · ⚪ só referência

---

## 1. CRM / Pipeline (substitui o Pipefy)

| Planilha | Link | Conteúdo | Uso no CRM | Status |
|---|---|---|---|---|
| **Análise - pipefy** | [abrir](https://docs.google.com/spreadsheets/d/1uvRYu8_xEyVtQLWDH_eLhcr_GXAXXL9a0fX9FLozHBs/edit) | 133 solicitações pagas do Pipefy (1S2026), R$ 150 mil, com Categoria (Esportes, Eventos, Produtos, Torcida, Geral/Repasses), Fase, Status, Criador, Data, Descrição, Valor | Base histórica do **Financeiro operacional**. Colunas mapeiam quase 1:1 para lançamentos de despesa | 🟡 |

## 2. Financeiro

| Planilha | Link | Conteúdo | Uso no CRM | Status |
|---|---|---|---|---|
| **Financeiro Atlética FGV Rio - 26.1** | [abrir](https://docs.google.com/spreadsheets/d/1C2eW38_DNbFnyAlag9G19Aqtcy-ZSmSFzsqAa-ADFcc/edit) | Lançamentos (Data, Área, Despesa/Receita, Valor, Descrição, Status, link do comprovante) + Orçado x Gasto por área + Fluxo de caixa + Resumo mensal. Áreas: **Eventos, Esportes, Produtos, Patrocínios, Torcida, Jogos, Investimentos, Outros, Administrativo** | É o **modelo exato** do módulo Financeiro (Fase 2). Serve para importar o histórico de lançamentos e para definir as categorias padrão | 🟢 (lançamentos) |
| **Orçamento Arena** | [abrir](https://docs.google.com/spreadsheets/d/1Xv73n7rq52sTgjmmhS_5lNHrvCQUMdV-sD1RRtFdthc/edit) | Orçamento de um evento/estrutura | Referência para orçamento de evento | ⚪ |

## 3. Festas e eventos  → alimenta o novo módulo **Eventos / Festas**

| Planilha | Link | Conteúdo | Uso no CRM | Status |
|---|---|---|---|---|
| **FRAT HOUSE 2026** | [abrir](https://docs.google.com/spreadsheets/d/1F0bWXpj24-EZYlvICc7Xq4vak5CMw4mGEJ6Y3IPIAxg/edit) | Lotes de ingresso (qtd, valor, total), custos fixos (local, som, segurança, DJ…), custos variáveis (bebidas por sabor, ml/pessoa), breakeven, resultado. Traz também FRAT HOUSE 2025 | **Estrutura-base da modelagem de Festas.** Cada bloco vira: lotes de ingresso, custos, resultado | 🟡 |
| **Jungle 2026** | [abrir](https://docs.google.com/spreadsheets/d/1PwHQFuzZA_MK7bHdPMC9N8jZVj-vVpQPEasV9uvkNww/edit) | Mesma lógica da Jungle (festa maior). 323 ingressos, R$ 32,7 mil | Festa → lotes + custos + resultado | 🟡 |
| **Jungle 2025** | [abrir](https://docs.google.com/spreadsheets/d/1ms_7gfE1GXsAok2MRTpZOC2RGJLyafCWeAEQ15eD12M/edit) | Histórico Jungle 2025 | Análise ano a ano | 🟡 |
| **Jungle 2024** | [abrir](https://docs.google.com/spreadsheets/d/1ETrGNcG44att6qHproDE8BAIrDKU9Q-tHwbFZYjrUcI/edit) | Histórico Jungle 2024 | Análise ano a ano | 🟡 |
| **COPA FGV 26** | [abrir](https://docs.google.com/spreadsheets/d/1g557_L_xIQq38GtB39vIOM28ExY3RJd_gA6IymCFlQ4/edit) | Campeonato esportivo (inscrições, chaves) | Evento tipo "Torneio" | 🟡 |
| **Atléticas Jogos RU 2026** | [abrir](https://docs.google.com/spreadsheets/d/1aAtbreW0bRP2BKByIUvPg7ifobKoKKycPsuHfRPEE1U/edit) | Jogos entre atléticas | Evento tipo "Jogos" | ⚪ |

## 4. Patrocínio / empresas → alimenta **Fornecedores** (categoria Patrocínio) e o pipeline de parcerias

| Planilha | Link | Conteúdo | Uso no CRM | Status |
|---|---|---|---|---|
| **Relação com Empresas** | [abrir](https://docs.google.com/spreadsheets/d/1D4sv6PVM3pjGCanbKLxaOrXsgS4lF3vgDej8ORwmfLg/edit) | ~66 empresas com contato focal, telefone, e-mail (Accenture, Ambev, BTG, Itaú, Nubank, Petrobras…) | **Import direto** para Fornecedores/Parceiros (categoria Patrocínio) ou lista de contatos de patrocínio | 🟢 |
| **[Contato] Empresas Parceiras** | [abrir](https://docs.google.com/spreadsheets/d/1B5z0_cqR5-eisvC3xkgj5ZxuNpGjh2jpY_25VBSBuno/edit) | Contatos de empresas parceiras (compartilhada) | Complementa a lista acima | 🟡 |

## 5. Membros / pessoas → alimenta **Clientes** (categorias Membro da Atlética / Atleta)

| Planilha | Link | Conteúdo | Uso no CRM | Status |
|---|---|---|---|---|
| **Relação Padrinhos e Membros** | [abrir](https://docs.google.com/spreadsheets/d/1z7SJNAzgGruUZMSU5xBrmzhb87BdPleHHlHsDcBvC38/edit) | Padrinhos e seus afilhados (apelidos, informal) | Cadastro de membros com vínculo padrinho→afilhado | 🟡 |
| **Basquete - Atlética FGV Rio 26.1** | [abrir](https://docs.google.com/spreadsheets/d/14soAv2d769Vff2qsTGjTjdwet6hMJtSK4z03SzLiuM4/edit) | Elenco de basquete | Clientes categoria "Atleta" | 🟡 |
| **Processo Seletivo Atlética FGV Rio 2024.2 (respostas)** | [abrir](https://docs.google.com/spreadsheets/d/1qS5XGo-WGrzuDAM1gzU_2PKIXaTCe7PZgCBWPTH4kwQ/edit) | Respostas do processo seletivo | Base de candidatos/interessados | ⚪ |

---

## Não relevantes para o CRM (acadêmico / pessoal)

Exercicios 30 e 33 · Simulacao_Survey_Multivariada · Planilha de Entrevistas 26.1 ·
Trabalho Contabilidade Gerencial · Códigos iFood · GUT EPO · Museu de Títulos JFin ·
Dossiê RioJunior · Planilha de Cogestão · Planilha aula e nota · e planilhas sem título.

## Próximos passos sugeridos

1. **Fornecedores/Patrocínio**: exportar "Relação com Empresas" em CSV e importar
   (o CRM já tem importador de clientes; farei um equivalente para fornecedores).
2. **Financeiro (Fase 2)**: usar "Financeiro Atlética FGV Rio - 26.1" como modelo
   e importar os lançamentos de "Análise - pipefy".
3. **Festas**: o novo módulo Eventos já nasce com a estrutura de lotes + custos +
   resultado das planilhas Jungle/FRAT, e escreve a aba **Festas** no Google
   Sheets para análise ano a ano.
