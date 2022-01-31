import modules
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import nltk
nltk.download('wordnet')
nltk.download("punkt")
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from time import sleep
import webbrowser
import re

file = open("sys.txt","r")
sys_contents = file.read()
exec(sys_contents)
file.close()

def start():
    clean_sys()
    keys = input('Please list any keywords you would like to have considered >> ')
    for key in [k for k in nltk.word_tokenize(keys)]:
        if re.sub(r'[^\w\s]', '', key) != "":
            add_keywords(re.sub(r'[^\w\s]', '', key))
    update('keywords')
    print('Starting OrgAI...')
    update_orgs()
    ai()

def update(var):
    global sys_contents
    x = sys_contents.split('\n')
    for ind in range(len(x)):
        if x[ind].split(' ')[0] == var:
            exec('x[ind] = var + " = " + str('+var+')')
            sys_contents = ("\n").join(x)
            file = open("sys.txt","w")
            file.write(sys_contents)
            file.close()
            return
    print("[!!!] keywords dictionary not found in sys.txt")

def clean_sys():
    clean('keywords', True)
    clean('orgs', True)
    clean('org_ranking', True)
    clean('ranked_orgs', True)

def clean(*args):
    # var = orgs, keywords, org_ranking
    if len(args) == 1:
        confirm = input('Are you sure that you want to clear your %s? [y or n] >> ' % args[0])
        if confirm != 'y':
            return
    exec('global '+args[0])
    exec(args[0]+".clear()")
    update(args[0])
    print(args[0]+' cleared.')

def load(driver):
    print('loading...')
    while True:
        sleep(0.25)
        try:
            button = driver.find_element_by_class_name('outlinedButton').find_element_by_tag_name('button')
            button.click()
        except:
            break

def org_r(driver):
    try:
        org_results = driver.find_element_by_id('org-search-results').find_element_by_tag_name('ul').find_element_by_tag_name('div').find_elements_by_css_selector("*")
    except:
        print('[!!!] Exception triggered. Loading again...')
        driver.get("https://boilerlink.purdue.edu/organizations")
        driver.implicitly_wait(1)
        load(driver)
        org_results = org_r(driver)
    return org_results

def rank_orgs(word_list):
    # Rank = average(Orgs_Frequency * Keywords_Weight / Keywords_Frequency)
    global org_ranking
    for org_ind in orgs:
        ranked_words = 1
        for word in orgs[org_ind][3]:
            if word in word_list and word in keywords:
                key_weight = keywords[word][0] if keywords[word][0] != None else 0
                key_freq = keywords[word][1]
                key_org_freq = orgs[org_ind][3][word]
                rank = key_org_freq * key_weight / key_freq
                org_ranking[org_ind][1] = org_ranking[org_ind][1] + rank
                ranked_words += 1
        org_ranking[org_ind][1] = org_ranking[org_ind][1] / ranked_words
    org_ranking = {k: v for k, v in sorted(org_ranking.items(), key=lambda item: item[1][1], reverse=True)}
    update('org_ranking')

def update_orgs():
    driver = webdriver.Safari()
    driver.get("https://boilerlink.purdue.edu/organizations")
    driver.implicitly_wait(1)
    load(driver)
    org_results = org_r(driver)
    print('loaded!')
    org_instance_size = len(driver.find_element_by_id('org-search-results').find_element_by_tag_name('ul').find_element_by_tag_name('div').find_element_by_tag_name('div').find_elements_by_css_selector("*")) + 1
    num_orgs = len(org_results)//org_instance_size
    for w in keywords:
        keywords[w][1] = None
    update('keywords')
    clean("org_ranking", True)
    print(str(num_orgs)+" organizations found.")
    print('updating data...')
    org_temp = {}
    global org_ranking
    for i in range(int(num_orgs)):
        link_block = org_results[i*10+1].get_attribute('href')
        description_block = org_results[i*10+9].text
        title_block = org_results[i*10+8].text
        words = [PorterStemmer().stem(WordNetLemmatizer().lemmatize(w)).lower() for w in nltk.word_tokenize(description_block) if w.lower() not in stopwords and w.isalnum()]
        word_freq = {w: words.count(w) for w in words}
        orgs[i] = [title_block, link_block, description_block, word_freq]
        org_found = [org_ind for org_ind in range(len(org_ranking)) if title_block == org_ranking[org_ind][0]]
        if not org_found:
            org_temp[i] = [title_block, 0]
        else:
            org_temp[i] = [title_block, org_ranking[1]]
        for w in words:
            if w not in keywords:
                keywords[w] = [None, word_freq[w]]
            elif keywords[w][1] == None:
                keywords[w][1] = word_freq[w]
            else:
                keywords[w][1] += word_freq[w]
    driver.quit()
    update('keywords')
    print('keywords updated.')
    update('orgs')
    print('orgs updated.')
    org_ranking = org_temp
    print('ranking organizations...')
    rank_orgs([k for k in keywords])
    print('ranked.')
    print('org_ranking updated.')
    print('done!')

def ai():
    if len(org_ranking) == 0:
        update_orgs()

    cmd = ''
    while cmd != 'quit':
        key_list = [k for k  in org_ranking]
        ind = 0
        while org_ranking[key_list[ind]][0] in ranked_orgs:
            ind += 1
        if ind == len(key_list) - 1:
            print('All organizations have been ranked.')
            break
        print('\n-----------------------------------')
        print(orgs[key_list[ind]][0])
        print(orgs[key_list[ind]][2])
        if(orgs[key_list[ind]][0] != org_ranking[key_list[ind]][0]):
            raise("Names do not match!")
        webbrowser.open_new_tab(orgs[key_list[ind]][1])
        org_rank = float(input('\nRank this organization by interest >> '))
        while org_rank > 1 or org_rank < 0:
            print('[!!!] Rank must be in the range of 0 to 1. Please try again.')
            w = float(input('Rank this organization by interest >> '))
        ranked_orgs[org_ranking[key_list[ind]][0]] = org_rank
        for w in orgs[key_list[ind]][3]:
            old_rank = keywords[w][0]
            if old_rank == None:
                keywords[w][0] = org_rank
            elif old_rank != 1:
                keywords[w][0] = (old_rank + org_rank) / 2
        update('keywords')
        rank_orgs([k for k in orgs[key_list[ind]][3]])
        update('ranked_orgs')
        cmd = input('Hit enter for next organization or type "quit" to end session. >> ')
    return 
        

def add_keywords(*keys):
    for k in keys:
        kls = PorterStemmer().stem(WordNetLemmatizer().lemmatize(k)).lower()
        w = float(input('Weight for keyword "%s" >> ' % kls))
        while w > 1 or w < 0:
            print('[!!!] Weight must be in the range of 0 to 1. Please try again.')
            w = float(input('Weight for keyword "%s" >> ' % kls))
        keywords[kls] = [w, None] if kls not in keywords else [w, keywords[kls][1]]
        update('keywords')

def remove_keywords(*keys):
    for k in keys:
        del keywords[k]
    update('keywords')

def list_keywords():
    print("%-14s  %s  %s" % ("Keyword", "Weight", "Frequency"))
    words = {w: [keywords[w][0], keywords[w][1]] if keywords[w][0] != None else [0, keywords[w][1]] for w in keywords}
    words = {k: v for k, v in sorted(words.items(), key=lambda item: item[1][0], reverse=True)}
    keys = [k for k in words]
    cmd = 'more'
    ind = 0
    while cmd == 'more' and ind * 10 < len(keys):
        if (ind * 10) + 10 > len(keys):
            for k in keys[ind * 10:len(keys)]:
                print("%-14s  %-6s  %s" % (k, str(words[k][0]), str(words[k][1])))
        else:
            for k in keys[ind * 10:(ind * 10) + 10]:
                print("%-14s  %-6s  %s" % (k, str(words[k][0]), str(words[k][1])))
        ind += 1
        cmd = input('Type "more" for more entries >> ')

def search_keywords(*keys):
    for k in keys:
        kls = PorterStemmer().stem(WordNetLemmatizer().lemmatize(k))
        if kls in keywords:
            print("keyword: %s,  weight: %s, frequency: %s" % (kls, str(keywords[kls][0]), str(keywords[kls][1])))
        else:
            print('\nKeyword "%s" not associated.' % kls)
            response = input('Would you like to add keyword "%s"? [y or n] >> ' % kls)
            if response == 'y':
                add_keywords(kls)

def org_info(org):
    org_num = org_find(org) if type(org) == str else int(org)
    print(orgs[org_num][0])
    print(orgs[org_num][2])
    webbrowser.open_new_tab(orgs[org_num][1])

def org_stats(org):
    org_num = org_find(org) if type(org) == str else int(org)
    print(orgs[org_num][0])
    print(orgs[org_num][3])
    print(org_ranking[org_num])
    print('Organization Rank: ', ranked_orgs[orgs[org_num][0]] if orgs[org_num][0] in ranked_orgs else None)

def org_find(org):
    for i in range(len(orgs)):
        if org in orgs[i][0]:
            return i
    print('[!!!] Organization not found.')

def list_orgs():
    r = {k: v for k, v in sorted(ranked_orgs.items(), key=lambda item: item[1], reverse=True)}
    for org in r:
        print("%3d  %-55s  %f" % (org_find(org), org, r[org]))
