import os

try:
    from pmatch import pama_translate, pama_apply
except:
    # if the user hasn't installed pyPMatch, then assume we can find it...
    # ... in the parent folder
    import site
    site.addsitedir("..")
    from pmatch import pama_translate, pama_apply

my_pama_file = os.path.join(".","increase_header_level.pama")

code, match_code = pama_translate(
    source=None,
    filename=my_pama_file
)

app=pama_apply(code, match_code)

def increase_header_level(elem, doc):
    return app.increase_header_level(elem,doc)

def main(doc=None):
    from panflute import run_filter
    return run_filter(increase_header_level, doc=doc)

if __name__ == "__main__":
    main()
