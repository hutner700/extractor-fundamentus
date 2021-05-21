import requests
from bs4 import BeautifulSoup
import pandas as pd
from flask import Flask, make_response
import numpy as np
import lxml



def extrator(ativo):
    #Ativo = String, esse tem que se encontrar no site FUNDAMENTUS.
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}
        r = requests.get(f'https://fundamentus.com.br/detalhes.php?papel={ativo}',headers=headers)
        soup = BeautifulSoup(r.text,'lxml')
        tables = soup.find_all('table')
        #Todas as informações em sua forma mais bruta e dificil possivel (Sigla para dataframes)
        dfs = []
        #Todas as informações semi-refinadas (lista de dicionarios) (Sigla para Dataframe media)
        dfm = []
        #Todas as informações finals (dicionario unico) (Sigla para dataframe Final) (Sei que não é uma dataframe)
        dff = {}
        for item in tables:
            dfs.append(pd.read_html(str(item).replace('?',''),decimal=',',thousands='.')[0])
        #Tabela retirada de https://fundamentus.com.br/detalhes.php?papel=VALE3
        #arrumando a 1 tabela -> onde contem de Papel até Vol&Méd
        papel = np.split(dfs[0],[2],axis=1)
        colunas = ['Caracteristica','Valor']
        for item in papel:
            for element in (item.to_numpy()):
                dfm.append({element[0]:element[1]})
        dfs.pop(0)
        #Tabela primaria terminada e colocada na lista de dicionarios dfm
        #Arrumando a 2 tabela -> onde contem de Valor de mercado até Nro. Ações
        valor = np.split(dfs[0], [2], axis=1)
        colunas = ['Caracteristica', 'Valor']
        for item in valor:
            for element in (item.to_numpy()):
                dfm.append({element[0]: element[1]})
        dfs.pop(0)
        #Finalizando a 2 tabela e colocada na lista de dicionarios dfm
        #Arrumando a 3 tabela -> Começa em Oscilações e vai até giró ativo
        #final
        varia = np.split(dfs[0],[2],axis=1)
        #forma reduzida de variações = osciladores +  indicadores fundamentalistas
        dfo = []
        #dataframe de osciladores
        varia[0],varia[1] = varia[0].drop([0],axis=0),varia[1].drop([0],axis=0)
        colunas = ['Marcação', 'Variação']

        for element in (varia[0].to_numpy()):
            dfm.append({f'Variacao em {element[0]}': element[1]})
        #finalizando os osciladores
        #dataframe de indicadores
        dfi = []
        colunas = ['Indicador', 'Numero']
        for element in (varia[1].to_numpy()):
            dfm.append({f'Indicador {element[0]}': element[1]})
            dfm.append({f'Indicador {element[2]}': element[3]})
        #dfm.append({'indicadores fundamentalistas': dfi})
        dfs.pop(0)
        #Finalizando extração de osciladores e indicadores
        #Inicializando extração dos Dados Balanços Patrimonial
        dfs[0] = dfs[0].drop([0],axis=0)
        #dataframe de Dados Balanços Patrimoniais
        dfb = []
        dfs[0] = np.split(dfs[0],[2],axis=1)
        colunas = ['Caracteristica', 'Valor']
        for item in dfs[0]:
            for element in (item.to_numpy()):
                dfm.append({element[0]: element[1]})
        dfs.pop(0)
        #Finalização dos Dados de Balancos Patrimoniais

        #Iniciando demonstrativo de resuldados:
        #demon (Demonstrativo) [0] se refere ao anual [1] ao trimestral
        demon = np.split(dfs[0],[2],axis=1)
        demon[0],demon[1] = demon[0].drop([0,1],axis=0),demon[1].drop([0,1],axis=0)
        for elemento in demon[0].to_numpy():
            dfm.append({f'{elemento[0]} anual':elemento[1]})
        demon.pop(0)
        for elemento in demon[0].to_numpy():
            dfm.append({f'{elemento[0]} trimestral':elemento[1]})


        #Finalização e transformação em um dicionario unico
        for caract in dfm:
            dff.update(caract)
        return dff
    except:
        return 'error'


app = Flask(__name__)
app.config.update(
    Testing=True,
    JSON_AS_ASCII = False,
    JSON_SORT_KEYS = False
)

@app.route("/ativo/<info>", methods=["GET"])
def buscar(info):
    a = extrator(info)
    if a != 'error':
        return make_response(a, 200)
    else:
        return make_response({"error": f" Ou o ativo {info} não pode ser encontrado, ou ouve algum erro na extração, favor tentar novamente ou contate um administrador"}, 404)


@app.errorhandler(404)
def resource_not_found(e):
    return make_response({"error": "Página não encontrada"}, 404)
