# Bibliotecas padrão do python
from pprint import pprint
import re

# Bibliotecas instaladas via pip
#   pip install cloudscraper scrapy simplejson
import simplejson as json
from cloudscraper import create_scraper
from scrapy import Selector

# URL do downdetector porque as monitorações variam para cada país
downdetector_url = 'https://downdetector.com.br'

# Mensagens de erro
erro_de_conexao = 'Não é possível coletar, falha de conexão ao downdetector!'
erro_de_parse = 'Não é possível coletar, html do site downdetector alterado!'

# Agente de Browser
user_agent_os = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
user_agent_browser = '(KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'

# Instância do Scrapper
scraper = create_scraper(
    browser={
        'custom': f'{user_agent_os} {user_agent_browser}'
    }
)

# Crio a lista final dos serviços e coletas para transformar em JSON
services = []

# Executo o scraper para a página de status que tem a lista dos serviços
try:
    get_list = scraper.get(downdetector_url + '/status').text
except Exception as e:
    print(erro_de_conexao)
    print(e)

# Filtro o local da lista específica de serviços
try:
    services_list = Selector(
        text=get_list).css('div.main-container').xpath('./div/div/ul').xpath('./li/a')
except Exception as e:
    print(erro_de_parse)
    print(e)

# Faço um loop em cima de todos os itens da lista de serviços
for href in services_list:
    # Inicializo o dicionário específico do serviço
    service = {}
    service['status'] = []
    service['errors'] = []
    service['problems'] = []

    # Busco nome do serviço limpo
    service_sanitized = href.attrib['href'].split('/')[2].replace('-', '_')

    # Busco o nome da aplicação e caminho da url de serviço
    try:
        service['application'] = href.xpath('./text()').get()
        service['url'] = downdetector_url + href.attrib['href']
    except Exception as e:
        print(erro_de_parse)
        print(e)

    # Executo o scraper para a página de status do serviço atual
    try:
        get_items = scraper.get(service['url']).text
    except Exception as e:
        print(erro_de_conexao)
        print(e)
    # Busco o status do serviço
    try:
        current_status = Selector(
            text=get_items
        ).xpath(
            '//div[@id="company"]'
        ).css(
            'div.entry-title::text'
        ).getall()
        service_status = {}

        service_status['status_key'] = 'status_' + service_sanitized
        service_status['status_item'] = re.sub(
            r'\n +', '', current_status[1]
        )

        service['status'].append(service_status)
    except Exception as e:
        print(erro_de_parse)
        print(e)

    # Filtro o local da lista específica de erros em serviços
    try:
        services_errors = Selector(
            text=get_items
        ).xpath(
            '//div[@id="indicators-card"]/div'
        ).css(
            'div.row'
        ).xpath(
            './div/div'
        )
    except Exception as e:
        print(erro_de_parse)
        print(e)

    # Faço um loop em cima de todos os itens de erros em serviços
    for error in services_errors:
        try:
            error_description = re.sub(
                r'\n +', '', error.css('div.text-muted::text').getall()[0]
            )
            pooling_value = re.sub(
                r'\n +', '', error.css(
                    'div.font-weight-bold::text').getall()[0]
            ).replace('\xa0', '').replace('%', '')
        except Exception as e:
            print(erro_de_parse)
            print(e)

        error_sanitized = re.sub(
            r'[^A-Za-z0-9]+', '', error_description
        ).lower()

        service_errors = {}

        service_errors['error_name'] = error_description
        service_errors['error_key'] = (
            service_sanitized + '_' + error_sanitized
        )
        service_errors['error_value'] = pooling_value

        service['errors'].append(service_errors)

    # Filtro o local da lista específica de erros em serviços
    try:
        problems = Selector(
            text=get_items
        ).xpath(
            '//div[@id="articles-card"]/a/span/text()'
        ).get()
    except Exception as e:
        print(erro_de_parse)
        print(e)

    service_problems = {}

    service_problems['problem_key'] = 'Problemas resolvidos'
    service_problems['problem_key'] = (
        'problem_' + service_sanitized
    )
    if problems is not None:
        service_problems['problem_value'] = problems.replace(':', '')

    service['problems'].append(service_problems)
    # Adiciono o serviço na lista final
    services.append(service)
    pprint(service)

# Apresento a lista final no formato JSON que o LLD espera
pprint(json.dumps(services))
