import cherrypy
import os
import json
import requests
import tabular

import sys
import hashlib
import cacheEDL
from datetime import datetime

################################ Sys parameters ###############################
serviceURL = sys.argv[1]
servicePort = int(sys.argv[2])

################################ Cache Loading ################################
# Instantiate Cache Class
cache = cacheEDL.CacheEDL()
        
cache_EDL = cache.load("EDL")


################################ Server Path ################################
BASE_HTML_PATH = "./multilang_html"
BASE_MULTILANG_NER_HTTP = 'http://dickens.seas.upenn.edu:4033/ner'
BASE_MULTILANG_EDL_HTTP = 'http://macniece.seas.upenn.edu:4032/edl'

# BASE_COGCOMP_HTTP = "http://macniece.seas.upenn.edu:4001/annotate"

def getBasicNER(lang,text):
    res_json = getMULTILANG_NER_BERT(lang,text)
    tokens = []
    endPositions = []
    if "tokens" in res_json:
        tokens = res_json["tokens"]
    if "sentences" in res_json:
        sentences = res_json["sentences"]
        if "sentenceEndPositions" in sentences:
            endPositions = sentences["sentenceEndPositions"]
    # print(tokens)
    return tokens, endPositions, res_json

'''
def getBasicCCG(text):
    input = {"views":"TOKENS","text":text}
    res_out = requests.get(BASE_COGCOMP_HTTP, params = input)
    # print(res_out.text)
    res_json = json.loads(res_out.text)
    tokens = []
    endPositions = []
    if "tokens" in res_json:
        tokens = res_json["tokens"]
    if "sentences" in res_json:
        sentences = res_json["sentences"]
        if "sentenceEndPositions" in sentences:
            endPositions = sentences["sentenceEndPositions"]
    # print(tokens)
    return tokens, endPositions
'''

def getBasics(annView):
    #input = {"views":"TOKENS","text":text}
    #res_out = requests.get(BASE_COGCOMP_HTTP, params = input)
    #res_json = json.loads(res_out.text)
    res_json = annView
    tokens = []
    endPositions = []
    if "tokens" in res_json:
        tokens = res_json["tokens"]
    if "sentences" in res_json:
        sentences = res_json["sentences"]
        if "sentenceEndPositions" in sentences:
            endPositions = sentences["sentenceEndPositions"]
    # print(tokens)
    return tokens, endPositions

def initView(myTabularView,lang,text):
    myTabularView.setText(text)
    # t,s = getBasicCCG(text)
    t,s,res_json = getBasicNER(lang,text)
    myTabularView.setTokens( t )
    myTabularView.setSentenceEnds( s )
    return res_json

'''
    NER EXAMPLE: 
    # curl -d '{"lang" : "rus", "model" : "bert", "text" : "В прошлом году я жил в Шампейне, штат Иллинойс. Тогда моей лучшей подругой была Дейзи Джонсон."}' -H "Content-Type: application/json" -X POST http://cogcomp.org/dc4033/ner/
'''

def getMULTILANG_NER_BERT(lang,text):
    input = {"lang":lang,"model":"bert","text":text}
    res_out = requests.get(BASE_MULTILANG_NER_HTTP, params = input)
    #print('==========')
    #print(res_out.text)
    #print('----------')
    res_json = json.loads(res_out.text)
    #print('==========')
    #print(res_json)
    #print('----------')
    return res_json

def getMULTILANG_NER_COGCOMP(lang,text):
    input = {"lang":lang,"model":"cogcomp","text":text}
    res_out = requests.get(BASE_MULTILANG_NER_HTTP, params = input)
    #print('==========')
    #print(res_out.text)
    #print('----------')
    res_json = json.loads(res_out.text)
    #print('==========')
    #print(res_json)
    #print('----------')
    return res_json

def getMULTILANG_EDL(lang,text):
    global cache_EDL
    hash_value = hashlib.sha1(text.encode()).hexdigest()

    if cache.count(cache_EDL) > 250:
        cache.write('EDL', cache_EDL)
        cache_EDL = cache.load('EDL')

    if hash_value in cache_EDL[lang].keys():
        res_json, cache_EDL = cache.read('EDL', cache_EDL, lang, hash_value)
    

    else:
        input = {"lang":lang,"text":text}
        headers = {'content-type': 'application/json'}
        try:
            res_out = requests.post(BASE_MULTILANG_EDL_HTTP, data = json.dumps(input) , headers=headers)
            #print('===============================')
            #print(BASE_MULTILANG_EDL_HTTP, input, headers)
            #print('-------------------------------')
            #print(res_out.text)
            #print('-------------------------------')
            # res = res_out.json()
            # return {}
            res_json = json.loads(res_out.text)
            # res_json = json.loads(res)
        except:
            res_json = None

        cache_EDL = cache.add('EDL', cache_EDL, lang, text, hash_value, res_json)

    return res_json

def processNER(myTabularView,lang,text):
    # print('>>>>>>>>>>>>>>>> processNER')
    annjson = initView(myTabularView, lang, text)
    # annjson = getMULTILANG_NER(lang,text)
    if "tokens" in annjson:
        myTabularView.setText(text)
        t,s = getBasics(annjson)
        myTabularView.setTokens( t ) # reset tokens in foreign language
        # myTabularView.setSentenceEnds( s )
        tokens = annjson["tokens"]
        if len(tokens) != len(myTabularView.getTokens()): return
        myTabularView.addSpanLabelView(annjson,"NER_CONLL","NER-Neural")
    '''    
    try:
        annjson2 = getMULTILANG_NER_COGCOMP(lang,text)
        if "text_annotation" in annjson2:
            annjson2 = annjson2["text_annotation"]
            if "tokens" in annjson2:
                #print(annjson2)
                #print("-----------")
                tokens = annjson2["tokens"]
                if len(tokens) != len(myTabularView.getTokens()): return
                myTabularView.addSpanLabelView(annjson2,"NER_CONLL","NER-CogComp")
    except Exception as e:
        print("An exception occurred when runnin CogComp NER")
        print(e)
    '''
    return annjson,tokens

def processEDL(myTabularView,lang,text,nerjson={}):
    # print('>>>>>>>>>>>>>>>> processEDL')
    annjson = getMULTILANG_EDL(lang,text)
    #if "tokens" in annjson:
    #    tokens = annjson["tokens"]
    #    if len(tokens) != len(myTabularView.getTokens()): return
    if True and annjson:
        myTabularView.addSpanList(annjson,"EDL","EDL")
    return annjson


'''
def getSRL_VERB(text):
    input = {"views":"SRL_VERB","text":text}
    res_out = requests.get(BASE_COGCOMP_HTTP, params = input)
    # print(res_out.text)
    res_json = json.loads(res_out.text)
    return res_json

def getSRL_NOM(text):
    input = {"views":"SRL_NOM","text":text}
    res_out = requests.get(BASE_COGCOMP_HTTP, params = input)
    # print(res_out.text)
    res_json = json.loads(res_out.text)
    return res_json

def getSRL_PREP(text):
    input = {"views":"SRL_PREP","text":text}
    res_out = requests.get(BASE_COGCOMP_HTTP, params = input)
    # print(res_out.text)
    res_json = json.loads(res_out.text)
    return res_json

def getRELATION(text):
    input = {"views":"RELATION","text":text}
    res_out = requests.get(BASE_COGCOMP_HTTP, params = input)
    # print(res_out.text)
    res_json = json.loads(res_out.text)
    return res_json

def getTIMEX3(text):
    input = {"views":"TIMEX3","text":text}
    res_out = requests.get(BASE_COGCOMP_HTTP, params = input)
    # print(res_out.text)
    res_json = json.loads(res_out.text)
    return res_json

def processSRL(myTabularView,text):
    annjson = getSRL_VERB(text)
    if "tokens" in annjson:
        tokens = annjson["tokens"]
        if len(tokens) != len(myTabularView.getTokens()): return
        myTabularView.addPredicateArgumentView(annjson,"SRL_VERB","SRL-Verb")
    annjson = getSRL_NOM(text)
    if "tokens" in annjson:
        tokens = annjson["tokens"]
        if len(tokens) != len(myTabularView.getTokens()): return
        myTabularView.addPredicateArgumentView(annjson,"SRL_NOM","SRL-Nom")
    annjson = getSRL_PREP(text)
    if "tokens" in annjson:
        tokens = annjson["tokens"]
        if len(tokens) != len(myTabularView.getTokens()): return
        myTabularView.addPredicateArgumentView(annjson,"SRL_PREP","SRL-Prep")

def processREL(myTabularView,text):
    annjson = getRELATION(text)
    if "tokens" in annjson:
        tokens = annjson["tokens"]
        if len(tokens) != len(myTabularView.getTokens()): return
        myTabularView.addRelationView(annjson,"RELATION","Relation")

def processTIM(myTabularView,text):
    annjson = getTIMEX3(text)
    if "tokens" in annjson:
        tokens = annjson["tokens"]
        if len(tokens) != len(myTabularView.getTokens()): return
        myTabularView.addSpanLabelView(annjson,"TIMEX3","Timex3")

'''

def doProcess(myTabularView, lang=None, text=None, anns=None):
    # print(">>>>>> PROCESS")
    myTabularView.reset()
    # initView(myTabularView, text) # DOES THE SENTENCE SPLITTER WORK FOR NON-ENGLISH TEXT?
    # for ann in anns:
    ann = "NER"
    nerjson = {}
    tokens = []
    # if True or ann in ["NER","EDL"]: 
    nerjson,tokens = processNER(myTabularView, lang, text)
    print("TOKENS",tokens)
    ann = "EDL"
    # if lang != "eng" and ann == "EDL": processEDL(myTabularView, lang, text, nerjson)
    h = ""
    # if lang not in ["eng","ned","deu","pl","uzb"] and "EDL" in anns: 
    if True or (lang not in ["eng"] and "EDL" in anns):
        edljson = processEDL(myTabularView, lang, text, nerjson)
        print(edljson)
        if not edljson:
            return '<div class="error">There was an error processing EDL for '+lang+'</div>'
        linkEDL = []
        linkEDLend = []
        for t in tokens:
            linkEDL.append("")
        for edl in edljson:
            print(edl["label"])
            param = edl["label"].split("|")
            if len(param) > 1:
                param = param[1]
            else:
                param = param[0]
            linkEDL[edl["start"]] = "https://en.wikipedia.org/wiki/"+param
            linkEDLend.append(edl["end"])
        print("LINK",linkEDL)
        print("Ends",linkEDLend)
        print("--")
        output = ""
        for i in range(len(tokens)):
            if i in linkEDLend:
                output += '</b></a>'
            output += " "    
            if linkEDL[i] != "":
                output += '<a href="'+linkEDL[i]+'" target="_blank"><b>'
            output += tokens[i]    
        if len(tokens) in linkEDLend:
            output += '</b></a>'
    # return json.dumps( myTabularView.getTokens() )
    h += myTabularView.HTML()
    h = '<div class="w3-panel w3-border w3-border-amber">'
    # h += " ".join(tokens)
    h += "<br>" + output + "<br>&nbsp;"
    h += '</div>'
    return h

class MyWebService(object):

    _myTabularView = None
    
    @cherrypy.expose
    def index(self):
        return open(BASE_HTML_PATH+'/index.php')

    def html(self):
        pass

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def info(self, **params):
        return {"status":"online"}

    @cherrypy.expose
    def halt(self, **params):
        cherrypy.engine.exit()


    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def view(self, text=None, lang=None, anns=None):
        input = { "lang" : None , "text" : None , "anns" : [] }
        try:
            data = cherrypy.request.json
        except:
            data = cherrypy.request.params
        if "lang" in data: input["lang"] = data["lang"]
        if "text" in data: input["text"] = data["text"]
        if "anns" in data: input["anns"] = data["anns"]
        # print(">>>>>>>>>", data["text"])
        self._myTabularView = tabular.TabularView()
        html = doProcess(self._myTabularView, data["lang"] , data["text"] , data["anns"])
        # return {"html":'<pre>'+json.dumps(input)+'</pre>'}
        result = {"input": input, "html": html}
        return result

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def showCache(self):
        result = cache_EDL
        return result

if __name__ == '__main__':
    print ("")
    print ("Starting 'Multilang' rest service...")
    config = {'server.socket_host': serviceURL}
    cherrypy.config.update(config)
    config = {
      'global' : {
            'server.socket_host' : serviceURL, #'dickens.seas.upenn.edu',
            'server.socket_port' : servicePort, #4031,
            'cors.expose.on': True
      },
      '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())

      },
      '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': BASE_HTML_PATH
      },
      '/html' : {
        'tools.staticdir.on'    : True,
        'tools.staticdir.dir'   : BASE_HTML_PATH,
        'tools.staticdir.index' : 'index.html',
        'tools.gzip.on'         : True
      },
    }
    cherrypy.config.update(config)
    cherrypy.quickstart(MyWebService(), '/', config)

    cache.write('EDL', cache_EDL)
