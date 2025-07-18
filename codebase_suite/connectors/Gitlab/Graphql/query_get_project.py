import textwrap

import urllib3

urllib3.disable_warnings()

def query_get_project():
    return textwrap.dedent('''\
        query($fullPath: ID!){
            project(fullPath: $fullPath) {
                id
                name
                archived
                ciConfigPathOrDefault
                description
                fullPath
                visibility
                avatarUrl
                topics
                branchRules {
                    nodes {
                        id
                        name
                        isDefault
                        branchProtection {
                            allowForcePush
                            pushAccessLevels {
                                nodes {
                                    accessLevel
                                    accessLevelDescription
                                }
                            }
                            mergeAccessLevels {
                                nodes {
                                    accessLevel
                                    accessLevelDescription
                                }
                            }
                        }
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
                labels {
                    nodes {
                        id
                        color
                        description
                        title 
                    }
                }
            }
        }
    ''')
   
