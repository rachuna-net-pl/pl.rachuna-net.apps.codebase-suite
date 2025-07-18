import textwrap

import urllib3

urllib3.disable_warnings()

def query_get_group():
    return textwrap.dedent('''\
        query($fullPath: ID!){
            group(fullPath: $fullPath) {
                id
                name
                fullPath
                description
                visibility
                avatarUrl
                labels {
                    nodes {
                        id
                        color
                        description
                        title 
                    }
                }
                ciVariables{
                    nodes {
                        id
                        key
                        description
                        value
                        protected
                        masked
                        environmentScope
                    }            
                }
            }
        }
    ''')
