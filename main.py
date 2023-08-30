import os
import tempfile
from flask import Flask, jsonify, request, session
from flask_httpauth import HTTPTokenAuth
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
auth = HTTPTokenAuth(scheme='Bearer')

temp_dir = tempfile.gettempdir()
user_tokens_file = os.path.join(temp_dir, 'user_tokens.txt')

def load_user_tokens():
    try:
        with open(user_tokens_file, 'r') as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        return []

def save_user_tokens(tokens):
    with open(user_tokens_file, 'w') as file:
        for token in tokens:
            file.write(token + '\n')

@auth.verify_token
def verify_token(token):
    user_tokens = load_user_tokens()
    if token in user_tokens:
        return token

def adicionar_usuario_na_lista(email):
    user_tokens = load_user_tokens()
    if email not in user_tokens:
        user_tokens.append(email)
        save_user_tokens(user_tokens)

taxa = 0.0103
taxa_conversao = 0.0033
meses = 12

principal = 1000000
aporte_mensal_a = 2000

aportes_adicionais = []

resultados = []

def calcular_resultados():
    global resultados, principal

    resultados = []

    for mes in range(1, meses + 1):
        aporte_b = next((aporte["valor"] for aporte in aportes_adicionais if aporte["mes"] == mes), 0)
        juros = (principal + aporte_mensal_a + aporte_b) * taxa
        saldo_final = principal + aporte_mensal_a + aporte_b + juros
        juros_reais = saldo_final * taxa_conversao

        resultados.append({
            'Mês': mes,
            'Saldo': round(principal, 2),
            'Aporte': round(aporte_mensal_a, 2),
            'Aporte+': round(aporte_b, 2),
            'Juros': round(juros, 2),
            'Saldo Final': round(saldo_final, 2),
            'Juros em Reais': round(juros_reais, 2)
        })

        principal = saldo_final

calcular_resultados()

@app.route('/api/resultados', methods=['GET'])
@auth.login_required
def obter_resultados():
    return jsonify(resultados)

@app.route('/api/editar', methods=['POST', 'PUT'])
@auth.login_required
def editar_configuracoes():
    global taxa, taxa_conversao, meses, principal, aporte_mensal_a, aportes_adicionais

    data = request.json

    taxa = data['taxa']
    taxa_conversao = data['taxa_conversao']
    meses = data['meses']
    principal = data['principal']
    aporte_mensal_a = data['aporte_mensal_a']

    aportes_adicionais_str = data.get('aportes_adicionais', '[]')
    aportes_adicionais = json.loads(aportes_adicionais_str)

    calcular_resultados()

    return jsonify({'message': 'Configurações editadas com sucesso.'})

@app.route('/api/adicionar_usuario', methods=['POST'])
def adicionar_usuario():
    data = request.json
    email = data.get('email')
    nome = data.get('nome')

    if email and nome:
        adicionar_usuario_na_lista(email)
        return jsonify({'message': 'Usuário adicionado com sucesso.'}), 201
    else:
        return jsonify({'error': 'Dados incompletos.'}), 400

@app.route('/api/saldos_finais_anuais', methods=['GET'])
@auth.login_required
def obter_saldos_finais_anuais():
    saldos_finais_anuais = []

    for resultado in resultados[11::12]:
        saldo_final_anual = resultado['Saldo Final']
        ano = resultado['Mês'] // 12
        saldos_finais_anuais.append({
            'ano': f'{ano}',
            'saldo_total': round(saldo_final_anual, 2)
        })

    return jsonify(saldos_finais_anuais)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
