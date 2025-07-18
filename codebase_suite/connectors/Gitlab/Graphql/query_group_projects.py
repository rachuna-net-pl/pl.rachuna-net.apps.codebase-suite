import textwrap

import urllib3

urllib3.disable_warnings()

def query_group_projects():
    return textwrap.dedent('''\
        query($after: String, $fullPath: ID!){
            group(fullPath: $fullPath) {
                projects(first: 100, includeSubgroups: true, after: $after, sort: PATH_DESC) {
                    nodes {
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
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
    ''')