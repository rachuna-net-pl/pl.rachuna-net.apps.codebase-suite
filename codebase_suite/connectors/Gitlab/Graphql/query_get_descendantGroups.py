import textwrap

import urllib3

urllib3.disable_warnings()

def query_get_descendantGroups():

    return textwrap.dedent('''\
        query($after: String, $fullPath: ID!){
            group(fullPath: $fullPath) {                        
                descendantGroups(first: 100, includeParentDescendants: true, after: $after, sort: PATH_DESC) {
                    nodes {
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
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
    ''')