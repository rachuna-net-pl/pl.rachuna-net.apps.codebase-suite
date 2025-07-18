import gitlab
import gitlab.exceptions
import urllib3

from .Exceptions import (
    GitlabInstanceUnavailableException,
    GitlabGraphQLUnavailableException
)
from .Graphql import (
    query_get_descendantGroups,
    query_get_group,
    query_get_project,
    query_group_projects
)

from ...config import Config
from ...core import Logger


urllib3.disable_warnings()


class GitlabConnector:
    """
    Klasa odpowiadająca za komunikacje z gitlab API i gitlab GRAPHQL
    """
    __logger: Logger
    __client = None
    __graphql = None
    __config = None
    _is_dry = False
    __cache = {}

    def __init__(self, logger: Logger = None) -> None:
        """
        Inicjalizuje połączenie z instancją Gitlab, uwierzytelnia klienta oraz tworzy obiekt GraphQL do wykonywania zapytań.

        :params config: Obiekt konfiguracji Gitlab (GitlabConfig)
        """
        if logger == None:
            self.__logger = Logger()
        else:
            self.__logger = logger
        self.__config = Config()
        
        self.__client = gitlab.Gitlab(
            url = self.__config.gitlab_url,
            private_token = self.__config.gitlab_token.get_secret_value(),
            ssl_verify = self.__config.ssl_verify,
            api_version = self.__config.api_version
        )
        self.__logger.trace(f"  Set gitlab url: {self.__config.gitlab_url}")
        self.__logger.trace(f"  Set gitlab token: {self.__config.gitlab_token.get_secret_value()}")
        self.__logger.trace(f"  Set gitlab api version: {self.__config.api_version}")
        self.__logger.trace(f"  Set gitlab ssl verify: {self.__config.ssl_verify}")

        try:
            self.__client.auth()
            self.__logger.debug("✔️  Authorization in Gitlab API successful.")
        except gitlab.exceptions.GitlabAuthenticationError as e:
            self.__logger.error("❌  Authorization Gitlab API failed. Please check your configuration.")
            raise GitlabInstanceUnavailableException
        
        try:
            self.__graphql = gitlab.GraphQL(
                url = self.__config.gitlab_url,
                token = self.__config.gitlab_token.get_secret_value(),
                ssl_verify = False,
            )
            self.__logger.debug("✔️  Authorization in Gitlab GRAPHQL successful.")
        except Exception as e:
            self.__logger.error("❌  Authorization Gitlab GRAPHQL failed. Please check your configuration.")
            raise GitlabGraphQLUnavailableException(e)

    # def set_is_dry(self, dry: bool) -> None:
    #     """
    #     Ustawia, czy operacje mają być wykonywane "na sucho" (dry-run).
        
    #     :params dry: Wartość logiczna określająca tryb dry-run
    #     :return: None
    #     """

    #     self._is_dry = dry

    def get_project_by_id(self, project_id: int):
        """
        Wykonuje zapytanie do API, aby pobrać project o podanym id.
        """
        return self.__client.projects.get(id=project_id)
    
    def get_group_by_id(self, group_id: int):
        """
        Wykonuje zapytanie do API, aby pobrać grupę o podanym id.
        """
        return self.__client.groups.get(id=group_id)


    def get_group_badges(self, full_path: str):
        """
        Wykonuje zapytanie do API, aby pobrać badges dla danej grupy
        """
        badges = []
        badges.extend(self.__client.groups.get(full_path).badges.list(all=True))
        
        return [badge.attributes for badge in badges]

    def get_project_badges(self, full_path: str):
        """
        Wykonuje zapytanie do API, aby pobrać badges dla danego projektu
        """
        badges = []
        badges.extend(self.__client.projects.get(full_path).badges.list(all=True))
        
        return [badge.attributes for badge in badges]

    def get_project_mirrors(self, project: str):
        """
        Wykonuje zapytanie do API, aby pobrać mirror dla danego projektu
        """
        project_obj = self.__client.projects.get(project)
        return project_obj.remote_mirrors.list()

    def get_project_protected_tags(self, full_path: str):
        """
        Wykonuje zapytanie do Api, aby pobrać protected tags dla danego projektu.
        """
        protected_tags = []
        protected_tags.extend(self.__client.projects.get(full_path).protectedtags.list(all=True))
        return [tag.attributes for tag in protected_tags]

    def graphql_get_group(self, full_path: str):
        """
        Wykonuje zapytanie GraphQl, aby pobrać informacje o grupie

        :params full_path: Nazwa (fullPath) grupy w Gitlab
        :return: Słownik zawierający wyniki zapytań GraphQL
        """
        cache_id = f"group:{full_path}"
        if cache_id not in self.__cache:
            variables = {
                'fullPath': full_path
            }
            if cache_id not in self.__cache:
                self.__cache[cache_id] = self.__graphql.execute(query_get_group(), variables)['group']
                self.__cache[cache_id]['ciVariables'] = self.__cache[cache_id]["ciVariables"]['nodes']
                for i in self.__cache[cache_id]['ciVariables']:
                    i['id'] = i['id'].replace("gid://gitlab/Ci::GroupVariable/","")
                self.__cache[cache_id]['labels'] = self.__cache[cache_id]["labels"]['nodes']
                for i in self.__cache[cache_id]['labels']:
                    i['id'] = i['id'].replace("gid://gitlab/GroupLabel/","")
                    i['id'] = i['id'].replace("gid://gitlab/ProjectLabel/","")
                self.__cache[cache_id]['id'] = self.__cache[cache_id]['id'].replace("gid://gitlab/Group/","")
        return self.__cache[cache_id]

    def graphql_get_descendantGroups(self, full_path: str):
        """
        Wykonuje zapytanie GraphQl, aby pobrać grupy potomne dla podanej grupy.
        dla wszystkich projektów w wybranej grupie.

        :params group: Nazwa (fullPath) grupy w Gitlab
        :return: Słownik zawierający wyniki zapytań GraphQL
        """
        after= None
        while True:
            variables = {
                'after': after,
                'fullPath': full_path
            }
            result = self.__graphql.execute(query_get_descendantGroups(), variables)['group']
            if result != None:
                for group in result['descendantGroups']['nodes']:
                    cache_id = f"group:{group['fullPath']}"
                    if not cache_id in self.__cache:
                        self.__cache[cache_id] = group
                        
                        self.__cache[cache_id]['ciVariables'] = self.__cache[cache_id]["ciVariables"]['nodes']
                        for i in self.__cache[cache_id]['ciVariables']:
                            i['id'] = i['id'].replace("gid://gitlab/Ci::GroupVariable/","")
                        
                        self.__cache[cache_id]['labels'] = self.__cache[cache_id]["labels"]['nodes']
                        for i in self.__cache[cache_id]['labels']:
                            i['id'] = i['id'].replace("gid://gitlab/GroupLabel/","")
                        
                        self.__cache[cache_id]['id'] = self.__cache[cache_id]['id'].replace("gid://gitlab/Group/","")
    
            if not result['descendantGroups']['pageInfo']['hasNextPage']:
                break
    
            after = result['descendantGroups']['pageInfo']['endCursor']

        ret = []
        for k in self.__cache:
            if k != f"group:{full_path}" and k.startswith(f"group:{full_path}"):
                ret.append(self.__cache[k])
        return ret

    def graphql_get_group_projects(self, full_path: str):
        """
        Wykonuje zapytanie GraphQl, aby pobrać informacje o wszystkich projektach w grupie.

        :params group: Nazwa (fullPath) grupy w Gitlab
        :return: Słownik zawierający wyniki zapytań GraphQL
        """
        after= None
        while True:
            variables = {
                'after': after,
                'fullPath': full_path
            }
            result = self.__graphql.execute(query_group_projects(), variables)['group']
            if result != None:
                for project in result['projects']['nodes']:
                    cache_id = f"project:{project['fullPath']}"
                    if not cache_id in self.__cache:
                        self.__cache[cache_id] = project
                        self.__cache[cache_id]['branchRules'] = self.__cache[cache_id]["branchRules"]['nodes']
                        for i in self.__cache[cache_id]['branchRules']:
                            i['id'] = i['id'].replace("gid://gitlab/Projects::AllBranchesRule/","")
                            i['id'] = i['id'].replace("gid://gitlab/Projects::BranchRule/","")
                            if i.get('branchProtection') is not None:
                                i['branchProtection']['pushAccessLevels'] = i['branchProtection']['pushAccessLevels']['nodes']
                                i['branchProtection']['mergeAccessLevels'] = i['branchProtection']['mergeAccessLevels']['nodes']
                        
                        self.__cache[cache_id]['ciVariables'] = self.__cache[cache_id]["ciVariables"]['nodes']
                        for i in self.__cache[cache_id]['ciVariables']:
                            i['id'] = i['id'].replace("gid://gitlab/Ci::Variable/","")
                        
                        self.__cache[cache_id]['labels'] = self.__cache[cache_id]["labels"]['nodes']
                        for i in self.__cache[cache_id]['labels']:
                            i['id'] = i['id'].replace("gid://gitlab/GroupLabel/","")

                        self.__cache[cache_id]['id'] = self.__cache[cache_id]['id'].replace("gid://gitlab/Project/","")
            if not result['projects']['pageInfo']['hasNextPage']:
                break
    
            after = result['projects']['pageInfo']['endCursor']

        ret = []
        for k in self.__cache:
            if k.startswith(f"project:{full_path}"):
                ret.append(self.__cache[k])
        return ret

    def graphql_get_project(self, full_path: str) -> dict:
        """
        Wykonuje zapytanie GraphQL, aby pobrać informacje o projekcie

        :param full_path: Nazwa (fullPath) projektu w Gitlab
        :return: Słownik zawierający wyniki zapytań GraphQL
        """
        cache_id = f"project:{full_path}"
        if not cache_id in self.__cache:
            variables = {
                'fullPath': full_path
            }
            if not cache_id in self.__cache:
                self.__cache[cache_id] = self.__graphql.execute(query_get_project(), variables)['project']
                self.__cache[cache_id]['branchRules'] = self.__cache[cache_id]["branchRules"]['nodes']
                for i in self.__cache[cache_id]['branchRules']:
                    i['id'] = i['id'].replace("gid://gitlab/Projects::AllBranchesRule/","")
                    i['id'] = i['id'].replace("gid://gitlab/Projects::BranchRule/","")
                    if i.get('branchProtection') is not None:
                        i['branchProtection']['pushAccessLevels'] = i['branchProtection']['pushAccessLevels']['nodes']
                        i['branchProtection']['mergeAccessLevels'] = i['branchProtection']['mergeAccessLevels']['nodes']
                
                self.__cache[cache_id]['ciVariables'] = self.__cache[cache_id]["ciVariables"]['nodes']
                for i in self.__cache[cache_id]['ciVariables']:
                    i['id'] = i['id'].replace("gid://gitlab/Ci::Variable/","")
                
                self.__cache[cache_id]['labels'] = self.__cache[cache_id]["labels"]['nodes']
                for i in self.__cache[cache_id]['labels']:
                    i['id'] = i['id'].replace("gid://gitlab/GroupLabel/","")

                self.__cache[cache_id]['id'] = self.__cache[cache_id]['id'].replace("gid://gitlab/Project/","")
        return self.__cache[cache_id]


    def get_project_inherited_variables(self,full_path: str):
        path = ""
        variables_by_key = {}

        for child_path in full_path.split('/'):
            path = child_path if path == "" else f"{path}/{child_path}"
            if full_path == path:
                variables = self.graphql_get_project(path)['ciVariables']
            else:
                variables = self.graphql_get_group(path)['ciVariables']
            for var in variables:
                key = var["key"] + ":" + var["environmentScope"] + ":" + str(var["protected"])
                var["path"] = path
                if (key in variables_by_key and
                    var["environmentScope"] == variables_by_key[key]["environmentScope"] and
                    var["protected"] == variables_by_key[key]["protected"]):
                        variables_by_key[key] = var
                else:
                    variables_by_key[key] = var
            
        return variables_by_key