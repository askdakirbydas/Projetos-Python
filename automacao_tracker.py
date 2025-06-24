from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import pandas as pd
import time
import os

# Acha o arquivo
service = Service(r"C:\Users\mares\Desktop\Projeto Python\chromedriver.exe")

# Caminho da pasta onde vai salvar os CSV
pasta = r'C:\Users\mares\Downloads\projeto_tracker'
os.makedirs(pasta, exist_ok=True)

driver = webdriver.Chrome(service=service)

driver.get('https://tracker.gg/valorant/premier/teams/b3cbd367-9f7d-44b2-83dd-a5617fe60da4/matches')
time.sleep(1) 

# Segunda janela
driver_overview = webdriver.Chrome(service=service)
driver_overview.get('https://tracker.gg/valorant/premier/teams/b3cbd367-9f7d-44b2-83dd-a5617fe60da4/overview')
time.sleep(1)

# Acha a div das partidas
match_table = driver.find_element(By.CSS_SELECTOR, 'div.v3-card__body.v3-card__body--v2\\.5')
rows = match_table.find_elements(By.CSS_SELECTOR, 'tr.match')

print(f"Encontrou {len(rows)} partidas!")

mapas, datas, adversarios, placar_time, placar_inimigo, resultado = [], [], [], [], [], []
nomes, scores = [], []

# Coleta dos players (overview)
players = driver_overview.find_elements(By.CSS_SELECTOR, '.player.trn-card.trn-card--bordered')
for p in players:
    try:
        nome = p.find_element(By.CSS_SELECTOR, '.player__profile').text.strip()
        score = p.find_element(By.CSS_SELECTOR, '.text-20.font-bold').text.strip()
        score = int(score.replace(',', '').replace('.', ''))
        nomes.append(nome)
        scores.append(score)
    except Exception as e:
        print("Erro ao coletar dados de um player:", e)
        continue

# Coleta das partidas
for row in rows:
    try:
        cols = row.find_elements(By.TAG_NAME, 'td')

        # Nome do mapa
        mapa_raw = cols[0].text.strip()
        splitado = mapa_raw.split('\n')
        mapa = splitado[0]
        data = splitado[1] if len(splitado) > 1 else 'Data não encontrada'

        adversario = cols[1].text.strip()

        # Placar
        score_raw = cols[2].text.strip().split('\n')
        score_self = int(score_raw[0])
        score_opp = int(score_raw[1])

        res = 'Vitória' if 'match--win' in row.get_attribute('class') else 'Derrota'

        mapas.append(mapa)
        datas.append(data)
        adversarios.append(adversario)
        placar_time.append(score_self)
        placar_inimigo.append(score_opp)
        resultado.append(res)

    except Exception as e:
        print("Erro na linha:", e)
        continue

driver.quit()
driver_overview.quit()

# data frame pandas
df = pd.DataFrame({
    'Data': datas,
    'Mapa': mapas,
    'Adversário': adversarios,
    'Placar_Time': placar_time,
    'Placar_Inimigo': placar_inimigo,
    'Resultado': resultado
})

print('\n--- Histórico das Partidas ---\n')
print(df)

# Winrate p/mapa
if not df.empty:
    winrate = df.groupby('Mapa')['Resultado'].value_counts().unstack(fill_value=0)
    winrate['Total'] = winrate.sum(axis=1)
    winrate['Winrate (%)'] = (winrate.get('Vitória', 0) / winrate['Total']) * 100

    print('\n--- Winrate por Mapa ---\n')
    print(winrate[['Vitória', 'Derrota', 'Total', 'Winrate (%)']].sort_values(by='Winrate (%)', ascending=False))

    # Winrate geral
    total_vitorias = (df['Resultado'] == 'Vitória').sum()
    total_partidas = len(df)
    winrate_total = (total_vitorias / total_partidas) * 100

    print(f'\n--- Winrate Total do Time ---\n')
    print(f'Total de partidas: {total_partidas}')
    print(f'Vitórias: {total_vitorias}')
    print(f'Derrotas: {total_partidas - total_vitorias}')
    print(f'Winrate Total: {winrate_total:.2f}%')

    # Resumo geral por mapa
    resumo_mapas = df.groupby('Mapa').agg({
        'Resultado': lambda x: (x == 'Vitória').sum(),
        'Placar_Time': 'sum',
        'Placar_Inimigo': 'sum',
        'Adversário': 'count'
    }).rename(columns={
        'Resultado': 'Vitórias',
        'Adversário': 'Partidas',
        'Placar_Time': 'Rounds Time',
        'Placar_Inimigo': 'Rounds Oponente'
    })

    resumo_mapas['Derrotas'] = resumo_mapas['Partidas'] - resumo_mapas['Vitórias']
    resumo_mapas['Winrate (%)'] = (resumo_mapas['Vitórias'] / resumo_mapas['Partidas']) * 100
    resumo_mapas = resumo_mapas[['Vitórias', 'Derrotas', 'Partidas', 'Rounds Time', 'Rounds Oponente', 'Winrate (%)']]
    resumo_mapas = resumo_mapas.sort_values(by='Winrate (%)', ascending=False)

    print('\n--- Resumo Geral dos Mapas ---\n')
    print(resumo_mapas)

    # Cria arquivo
    caminho_historico = os.path.join(pasta, 'historico_partidas.csv')
    caminho_winrate = os.path.join(pasta, 'winrate_por_mapa.csv')
    caminho_resumo = os.path.join(pasta, 'resumo_geral_mapas.csv')
    caminho_mvp = os.path.join(pasta, 'mvp_total.csv')

    df.to_csv(caminho_historico, index=False)
    winrate.to_csv(caminho_winrate)
    resumo_mapas.to_csv(caminho_resumo)

    print(f'\nCSVs salvos em:\n{caminho_historico}\n{caminho_winrate}\n{caminho_resumo}')

else:
    print('\nNenhuma partida encontrada.')

#Data frame mvp
df_players = pd.DataFrame({
    'Player': nomes,
    'Tracker Score': scores
}).sort_values(by='Tracker Score', ascending=False)

print('\nTracker Score dos Players\n')
print(df_players)

df_players.to_csv(caminho_mvp, index=False)
print(f'\nCSV do MVP salvo em:\n{caminho_mvp}')

# Acha o mvp
mvp = df_players.iloc[0]
print(f"\nO MVP é {mvp['Player']} com {mvp['Tracker Score']} de TRN Score!\n")
