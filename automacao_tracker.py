from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import pandas as pd
import time

# Acha o arquivo
service = Service(r"C:\Users\mares\Desktop\Projeto Python\chromedriver.exe")
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

mapas, adversarios, placar_time, placar_inimigo, resultado = [], [], [], [], []

nomes = []
scores = []

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

for row in rows:
    try:
        cols = row.find_elements(By.TAG_NAME, 'td')

        mapa = cols[0].text.strip()
        adversario = cols[1].text.strip()

        # Placar
        score_raw = cols[2].text.strip().split('\n')
        score_self = int(score_raw[0])
        score_opp = int(score_raw[1])

        res = 'Vitória' if 'match--win' in row.get_attribute('class') else 'Derrota'

        # Adiciona nas lista
        mapas.append(mapa)
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

    # Cria arquivo
    df.to_csv('historico_partidas.csv', index=False)
    winrate.to_csv('winrate_por_mapa.csv')

    print('\nDados CSV salvos')
else:
    print('\nNenhuma partida encontrada.')

#Data frame mvp
df_players = pd.DataFrame({
    'Player': nomes,
    'Tracker Score': scores
}).sort_values(by='Tracker Score', ascending=False)

print('\nTracker Score dos Players\n')
print(df_players)

# Acha o mvp
mvp = df_players.iloc[0]
print(f"\nO MVP é {mvp['Player']} com {mvp['Tracker Score']} de TRN Score!\n")

