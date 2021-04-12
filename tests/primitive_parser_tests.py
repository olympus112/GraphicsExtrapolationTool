from parsing.primitive_parser import PrimitiveParser

def test_master():
    r = PrimitiveParser.parse("""
        line(10, 10, 10, 10). 
        !p(10).
        { 
            rect(20, 20, 20, 20). 
            !p(2).
            {
                !snoepie(poepie).
            }
        }
    """)
    print(r)
    print(r.master)
    print(r[1].master)
    print(r[2].master)