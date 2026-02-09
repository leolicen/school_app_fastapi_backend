import json



def print_json_response(json_response, response_name: str, indentation: int = 2, separator: bool = True):
    """ Print a clearly formatted JSON response.

        Args: 
            json_response: Dictionary or JSON serializable object
            response_name: Name of the specific response
    """
    try:
        if separator:
            print("\n" + "="*50)
            
        print(f"\n{response_name}:\n")
        print(json.dumps(json_response, indent=indentation, ensure_ascii=False))
        
        if separator:
            print("\n" + "="*50)
        
    except TypeError:
        print(f"Object not serializable: {json_response}")