import re
from symspellpy import SymSpell, Verbosity
import pkg_resources
import streamlit as st

ABBREVIATIONS = {
    "u": "you", "r": "are", "ur": "your", "cn": "can", "cud": "could",
    "shud": "should", "wud": "would", "abt": "about", "bcz": "because",
    "plz": "please", "pls": "please", "tmrw": "tomorrow", "wat": "what",
    "wats": "what is", "info": "information", "yr": "year", "sem": "semester",
    "admsn": "admission", "clg": "college", "sch": "school", "uni": "university",
    "cresnt": "crescent", "l": "level", "d": "the", "msg": "message",
    "idk": "i don't know", "imo": "in my opinion", "asap": "as soon as possible",
    "dept": "department", "reg": "registration", "fee": "fees", "pg": "postgraduate",
    "app": "application", "req": "requirement", "nd": "national diploma",
    "a-level": "advanced level", "alevel": "advanced level", "2nd": "second",
    "1st": "first", "nxt": "next", "prev": "previous", "exp": "experience",
    "csc": "computer science", "mass comm": "mass communication", "acc": "accounting"
}

SYNONYMS = {
    "lecturers": "academic staff", "professors": "academic staff",
    "teachers": "academic staff", "instructors": "academic staff",
    "tutors": "academic staff", "staff members": "staff", "hod": "head of department",
    "school": "university", "college": "faculty", "course": "subject",
    "class": "course", "subject": "course", "unit": "credit",
    "credit unit": "unit", "course load": "unit", "non teaching": "non-academic",
    "admin worker": "non-academic staff", "support staff": "non-academic staff",
    "hostel": "accommodation", "lodging": "accommodation", "room": "accommodation",
    "school fees": "tuition", "acceptance fee": "admission fee", "fees": "tuition",
    "enrol": "apply", "join": "apply", "sign up": "apply", "admit": "apply",
    "requirement": "criteria", "conditions": "criteria", "needed": "required"
}

@st.cache_resource
def get_sym_spell():
    sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    dictionary_path = pkg_resources.resource_filename("symspellpy", "frequency_dictionary_en_82_765.txt")
    sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
    return sym_spell

def normalize_text(text):
    text = re.sub(r'[^\w\s\-]', '', text)  # keep hyphen
    text = re.sub(r'(.)\1{2,}', r'\1', text)  # remove repeated characters
    return text.lower()

def apply_abbreviations(words):
    return [ABBREVIATIONS.get(w.lower(), w) for w in words]

def apply_synonyms(words):
    return [SYNONYMS.get(w.lower(), w) for w in words]

def preprocess_text(text, debug=False):
    text = normalize_text(text)
    words = text.split()

    expanded = apply_abbreviations(words)

    sym_spell = get_sym_spell()
    corrected = []
    for word in expanded:
        suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
        corrected.append(suggestions[0].term if suggestions else word)

    final_words = apply_synonyms(corrected)

    if debug:
        print("Original:", text)
        print("Expanded:", expanded)
        print("Corrected:", corrected)
        print("With Synonyms:", final_words)

    return ' '.join(final_words)
