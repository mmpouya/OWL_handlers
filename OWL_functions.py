import re
import os
from typing import Dict
from dotenv import loaddotenv
from SPARQLWrapper import SPARQLWrapper , RDF , JSON
import json
# from rdflib.plugins.sparql import JSON
import io
import tokenize




def replace_resources_OWL (triples: str):
    triples = triples.replace("go:hasName", "rdfs:label")
    triples = triples.replace("go:hasDescription", "rdfs:label")
    triples = triples.replace("gov:", "go:")
    triples = triples.replace("go:event", "go:Event")
    triples = triples.replace("go:information", "go:Information")
    triples = triples.replace("go:information", "go:Document")
    triples = triples.replace("go:Entity", "go:Substance")
    triples = triples.replace("go:time", "go:Time")
    triples = triples.replace("go:substance", "go:Substance")
    triples = triples.replace("go:quality", "go:Quality")
    
    return triples

def adding_labels(triples, Labels:(Dict|None) = None):
    if not Labels:
        Labels = {"go:Event": "go:Event rdfs:label \"رخداد\"@fa.",
                    "go:Information": "go:Information rdfs:label \"اطلاعات\"@fa.",
                    "go:Time" : "go:Time rdfs:label \"زمان\"@fa.",
                    "go:Substance":"go:Substance rdfs:label \"شی\"@fa.",
                    "go:Quality":"go:Quality rdfs:label \"ویژگی\"@fa.",
                    "go:Agent": "go:Agent rdfs:label \"عامل\"@fa.", 
                    "go:Organization": "go:Organization rdfs:label \"سازمان\"@fa."}
    for node in Labels:
        if node in triples:
            triples = triples + "\n" + Labels[node]
    return triples

def remove_prefixes(ttl_text:str):
    lines = ttl_text.splitlines()
    # Filter out lines beginning with '@prefix'. We strip leading whitespace.
    filtered_lines = [line for line in lines if not line.lstrip().startswith("@prefix")]
    ttl_text= "\n".join(filtered_lines) 
    return ttl_text

def modify_prefixes(ttl_text:str,id:str):
    """
    Remove prefix declarations from a TTL file string.
    replace resources
    Parameters:
        ttl_text (str): TTL file content as a string.    
    Returns:
        str: TTL content with standard prefix declarations.
    """
    lines = ttl_text.splitlines()
    
    # Filter out lines beginning with '@prefix'. We strip leading whitespace.
    filtered_lines = [line for line in lines if not line.lstrip().startswith("@prefix")]
    ttl_text= "\n".join(filtered_lines)    
    intro = f"""@prefix : <http://majles.tavasi.ir/graph/> .
@prefix ex: <http://majles.tavasi.ir/graph/example/{id}#> .
@prefix bt: <http://borhan-onto.ir/ontology/time#> .
@prefix go: <http://majles.tavasi.ir/ontology#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
"""
    # ttl_text = retrieve_ontology_labels(ttl_text)   
    rdf = intro + "\n" + ttl_text
    return rdf

def get_qanon (section_id):
    with open("data/section_to_qanon.json", 'r', encoding="utf-8") as qanon_sections:
        data = json.load(qanon_sections)
    qanon_id = data[section_id]
    return qanon_id

def json_query_endpoint(query):
    """
    Executes a SPARQL query against a specified Virtuoso endpoint.

    Args:
        endpoint_url (str): The URL of the SPARQL endpoint.
        query (str): The SPARQL query to execute.

    Returns:
        dict: The query results in JSON format, or None if an error occurs.
    """
    loaddotenv()
    endpoint_url = os.getenv("SPARQL_ENDPOINT")
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def ttl_query_endpoint(query,endpoint_url):
    """
    Executes a SPARQL query against a specified Virtuoso endpoint.
    Args:
        endpoint_url (str): The URL of the SPARQL endpoint.
        query (str): The SPARQL query to execute.
    Returns:
        str: The ttl results in str format, or None if an error occurs.
    """
    loaddotenv()
    endpoint_url = os.getenv("SPARQL_ENDPOINT")
    sparql = SPARQLWrapper(endpoint_url)
    
    sparql.setQuery(query)
    try:
        ret = sparql.queryAndConvert()

        # ret.serialize(format="text/turtle")
        x = ret.serialize(format="text/turtle")
        # print(x)
        return x
    except Exception as e:
        print("error")
        print(e)

def retrieve_ontology_labels(ttl):
    sparql_query = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?s ?o
WHERE {
    ?s rdfs:label ?o .
}
"""
    query_results = json_query_endpoint(sparql_query)
    if query_results:
        # print("\n--- Query Results ---")
        # print(query_results)
        labels = {}
        for result in query_results["results"]["bindings"]:
            subject = result.get("s", {}).get("value", "N/A")
            obj = result.get("o", {}).get("value", "N/A")
            labels[subject] = subject + " rdfs:label "+ obj            
    ttl = adding_labels (ttl,labels)
    # print(labels)
    return ttl

def choosing (ttl: str, length: int = 20) -> str:
    lines = ttl.splitlines()
    filtered_lines = lines[:length]
    ttl = "\n".join(filtered_lines)
    return ttl

def extracted_used_prefixes(ttl_content:str) -> set:
    '''
    return a set of prefixes used in a ttl content(str)'''
    used_prefixes = set(re.findall(r'\b([a-zA-Z][\w\-]*)\:', ttl_content))
    return used_prefixes

def extract_prefixes(ttl_string:str) -> dict:
    """
    Extracts all @prefix declarations from a TTL string.

    Parameters:
        ttl_string (str): The Turtle file content as a string.

    Returns:
        dict: A dictionary mapping prefix labels to their URIs.
    """
    prefix_pattern = r'@prefix\s+([^\s:]+):\s+<([^>]+)>\s*\.'
    matches = re.findall(prefix_pattern, ttl_string)
    
    prefix_dict = {prefix: uri for prefix, uri in matches}
    return prefix_dict

def find_undeclared_prefixes(ttl_content: str) -> set:
    # Step 1: Find all declared prefixes via @prefix or PREFIX
    declared_prefixes = set(re.findall(r'@prefix\s+([a-zA-Z][\w\-]*)\s*:', ttl_content))
    declared_prefixes.update(re.findall(r'PREFIX\s+([a-zA-Z][\w\-]*)\s*:', ttl_content))
    
    # Step 2: Find all used prefixes in triples (e.g., rdf:type, foaf:name)
    # This regex finds things like foaf:name, ex:Person, etc.
    used_prefixes = set(re.findall(r'\b([a-zA-Z][\w\-]*)\:', ttl_content))
    
    # Step 3: Remove the declared ones
    undeclared_prefixes = used_prefixes - declared_prefixes
    
    return undeclared_prefixes


def shorten_IRIs_by_prefix(prefixes: dict, text: str) -> str:
    # Sort by descending length to avoid partial overlaps (e.g., "http://example.org/" before "http://example.org/foo/")
    sorted_prefixes = sorted(prefixes.items(), key=lambda x: -len(x[1]))
    
    def replacer(match):
        iri = match.group(1)
        for prefix, full_iri in sorted_prefixes:
            if iri.startswith(full_iri):
                return f"{prefix}:{iri[len(full_iri):]}"
        return f"<{iri}>"  # Leave untouched if no match

    return re.sub(r'<([^>]+)>', replacer, text)

def strip_comments_and_strings(ttl_content: str) -> str:
    """
    Return ttl_content with:
      - all comments removed
      - all string literals removed
    Preserves original spacing and line breaks.
    """
    out = []                # output characters
    i = 0
    n = len(ttl_content)

    # States
    IN_NONE = 0
    IN_COMMENT = 1
    IN_STRING = 2

    state = IN_NONE
    string_delim = None     # will be "'" or '"' or "'''" or '"""'
    while i < n:
        c = ttl_content[i]

        if state == IN_NONE:
            # start of comment?
            if c == "#" :
                state = IN_COMMENT
                out.append(" ")  # replace # with space
                i += 1
            # start of string?
            elif c in ("'", '"'):
                # check for triple-quote
                if i + 2 < n and ttl_content[i : i + 3] == c * 3:
                    string_delim = c * 3
                    state = IN_STRING
                    out.extend("   ")  # three spaces
                    i += 3
                else:
                    string_delim = c
                    state = IN_STRING
                    out.append(" ")     # single quote → single space
                    i += 1
            else:
                # normal character
                out.append(c)
                i += 1

        elif state == IN_COMMENT:
            # consume until end of line
            if c == "\n":
                state = IN_NONE
                out.append("\n")
            else:
                # replace comment char with space to preserve col pos
                out.append(" ")
            i += 1

        elif state == IN_STRING:
            # looking for end of string_delim
            dl = len(string_delim)
            if string_delim in ("'''", '"""'):
                # triple-quoted: can't be escaped
                if i + 2 < n and ttl_content[i : i + 3] == string_delim:
                    out.extend("   ")
                    i += 3
                    state = IN_NONE
                else:
                    # preserve newlines, blank out others
                    if c == "\n":
                        out.append("\n")
                    else:
                        out.append(" ")
                    i += 1
            else:
                # single-quoted string: handle backslash escapes
                if c == "\\" and i + 1 < n:
                    # backslash + next char → two spaces
                    out.extend("  ")
                    i += 2
                elif c == string_delim:
                    out.append(" ")
                    i += 1
                    state = IN_NONE
                else:
                    if c == "\n":
                        # technically stray newline in single-quoted is end of literal in TTL
                        # we treat it as out of string so that it doesn't gobble whole file
                        state = IN_NONE
                        out.append("\n")
                        i += 1
                    else:
                        out.append(" ")
                        i += 1

    return "".join(out)

def find_prefixes(ttl_content: str) -> set:
    '''
    return a set of prefixes used in a ttl content(str)'''
    if ttl_content.endswith(".ttl"):
        with open (ttl_content, 'r', encoding='utf-8')as file:
            data = file.read()
        # used_prefixes = []
        # for line in data:
        #     if line.strip().startswith("#"):
        #     # if line.startswith("#"):
        #         pass
                
        #     else:
        #         # print("line that is not comment")
        #         new_prefixes = re.findall(r'\b([a-zA-Z][\w\-]*)\:', line)
        #         used_prefixes = used_prefixes + new_prefixes
        # used_prefixes_set = sorted(set(used_prefixes))
        # return used_prefixes_set
        ttl_content = strip_comments_and_strings(data)
    else:
        pass
    used_prefixes = set(re.findall(r'\b([a-zA-Z][\w\-]*)\:', ttl_content))
    used_prefixes.remove("http")
    used_prefixes.remove("https")
    return used_prefixes

def prefix_cleaner (ttl_content:str) -> str:
    if ttl_content.endswith(".ttl"):
        with open (ttl_content, 'r', encoding='utf-8')as file:
            ttl_content = file.read()
    
    prefix_list = sorted(extracted_used_prefixes(ttl_content))
    standard_prefixes = ['owl', 'go', 'xsd', 'ex', 'rdfs', 'foaf', 'rdf', 'bt', 'time', 'xml']
    for prefix in prefix_list:
        if prefix in standard_prefixes:
            pass
        else:
            ttl_content = ttl_content.replace(prefix,'go')
    return ttl_content

if __name__ == "__main__":
    print(retrieve_ontology_labels(""))
