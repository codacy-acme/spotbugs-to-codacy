#!/usr/bin/env python3

import argparse
from bs4 import BeautifulSoup
import requests
import json
import time


def postResults(commitUuid, payload, projectToken, baseUrl):
    url = f'{baseUrl}/2.0/commit/{commitUuid}/issuesRemoteResults'
    headers = {
        'content-type': 'application/json',
        'project-token': projectToken
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print(response)
    print(response.text)



def resultsfinal(commitUuid, projectToken, baseUrl):
    url = f'{baseUrl}/2.0/commit/{commitUuid}/resultsFinal'
    headers = {
        'content-type': 'application/json',
        'project-token': projectToken
    }
    response = requests.post(url, headers=headers)
    print(response)
    print(response.text)


def loadPatterns(baseUrl):
    shortName = 'spotbugs'
    url = f'{baseUrl}/api/v3/tools'
    headers = {
        'content-type': 'application/json',
    }
    tools = json.loads(requests.get(url, headers=headers).text)['data']
    spotbugs = next(item for item in tools if item["shortName"] == shortName)
    patternsUrl = f'{baseUrl}/api/v3/tools/{spotbugs["uuid"]}/patterns?limit=1000'
    headers = {
        'content-type': 'application/json',
    }
    patterns = json.loads(requests.get(patternsUrl, headers=headers).text)['data']
    return patterns


def checkLevelForPattern(patterns, patternId):
    for p in patterns:
        if p['id'] == patternId:
            return p['level']
    return ''


def checkMessageForPattern(patterns, patternId):
    for p in patterns:
        if p['id'] == patternId:
            return p['title']
    return ''


def checkCategoryForPattern(patterns, patternId):
    for p in patterns:
        if p['id'] == patternId:
            return p['category']
    return ''


def process(reportPath, commitUuid, projectToken, baseDir, baseUrl,):
    patterns = loadPatterns(baseUrl)
    with open(reportPath, 'r') as f:
        data = f.read()
        Bs_data = BeautifulSoup(data, "xml")
        srcDir = Bs_data.find('SrcDir').text
        if not baseDir.endswith('/'):
            baseDir = baseDir+'/'
        srcDir = srcDir.replace(baseDir, '')
        bug_instances = Bs_data.find_all('BugInstance')
        bugs = []
        for bi in bug_instances:
            type = bi.get('type')
            sourceLine = bi.find('SourceLine', recursive=False).get('start')
            sourcePath = bi.find(
                'SourceLine', recursive=False).get('sourcepath')
            message = bi.find('LongMessage').text
            # print(bi)
            #print(type, sourceLine, sourcePath, message)
            bugs.append({
                'source': srcDir+'/'+sourcePath,
                'line': sourceLine,
                'type': type,
                'message': checkMessageForPattern(patterns, type),
                'level': checkLevelForPattern(patterns, type),
                'category': checkCategoryForPattern(patterns, type)
            })

        groups = {}
        for obj in bugs:
            if(not obj['source'] in groups):
                groups[obj['source']] = {
                    'filename': obj['source'],
                    'results': []
                }
            groups[obj['source']]['results'].append(
                {
                    'Issue': {
                        'patternId': {
                            'value': obj['type']
                        },
                        'filename': obj['source'],
                        'message': {
                            'text': obj['message']
                        },
                        'level': obj['level'],
                        'category': obj['category'],
                        'location': {
                            "LineLocation": {
                                "line": int(obj['line'])
                            }
                        }

                    }
                }
            )

        payload = [{
            'tool': 'spotbugs',
            'issues': {
                'Success': {
                    'results': list(groups.values())
                }
            }
        }]
       
        postResults(commitUuid, payload, projectToken, baseUrl)
        time.sleep(5)
        resultsfinal(commitUuid, projectToken, baseUrl)


def main():
    print('Welcome to Codacy Spotbugs Parser')
    parser = argparse.ArgumentParser(description='Codacy Spotbugs Parser')
    parser.add_argument('--report-path', dest='reportPath',
                        default=None, help='path to the spotbugs report')
    parser.add_argument('--project-token', dest='projectToken', default=None,
                        help='the project-token to be used on the REST API')
    parser.add_argument('--commit-uuid', dest='commitUuid', default=None,
                        help='the commit uuid')
    parser.add_argument('--basedir', dest='baseDir',
                        default=None, help='where code is clonned')
    parser.add_argument('--baseurl', dest='baseUrl', default='https://api.codacy.com',
                        help='codacy server address (ignore if cloud)')
    args = parser.parse_args()
    process(args.reportPath,args.commitUuid, args.projectToken, args.baseDir, args.baseUrl)


main()
