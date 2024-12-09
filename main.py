import autogen
from typing import List, Tuple, Set
import asyncio
import os
import json


config_list = (
    {
        'model': 'gpt-4',  # or 'gpt-3.5-turbo' 
        'api_key': os.getenv("OPENAI_API_KEY")  
    })



llm_config = (
        {
         "model": "bartowski/Llama-3.2-3B-Instruct-GGUF",
            "base_url": "http://localhost:1234/v1",
            "api_key": "lm-studio",
        }
)

MAZE = [
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]
]

START = (0, 0)
END = (14, 14)

class MazeEnvironment:
    #Handles the maze state and valid moves
    def __init__(self):
        self.maze = MAZE
        self.visited = set([START])
        self.start = START
        self.end = END
        
    def get_valid_moves(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        x, y = position
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        valid_moves = []
        
        for dx, dy in directions:
            new_pos = (x + dx, y + dy)
            if (0 <= new_pos[0] < len(self.maze) and 
                0 <= new_pos[1] < len(self.maze[0]) and 
                self.maze[new_pos[0]][new_pos[1]] == 0):
                valid_moves.append(new_pos)
                
        return valid_moves
    
    def visualize(self, active_positions):
        os.system('cls' if os.name == 'nt' else 'clear')
        for i in range(len(self.maze)):
            for j in range(len(self.maze[0])):
                pos = (i, j)
                if pos == self.start:
                    print("🔵", end=" ")
                elif pos == self.end:
                    print("🔴", end=" ")
                elif pos in active_positions:
                    print("🟢", end=" ")
                elif pos in self.visited:
                    print("·", end=" ")
                elif self.maze[i][j] == 1:
                    print("█", end=" ")
                else:
                    print(" ", end=" ")
            print()
        print("\nLegend: 🔵=Start 🔴=End 🟢=Agent ·=Visited █=Wall")

class ExplorerAgent:
    def __init__(self, position: Tuple[int, int], explorer_id: int):
        system_message = f"""You are maze explorer {explorer_id}. You navigate through a maze trying to reach the goal.
        Your decisions should be based on:
        1. Available valid moves
        2. Your current position
        3. The goal position
        4. Your exploration history
        
        Respond with a JSON object containing:
        {{"action": "move", "direction": <chosen_direction>}}
        or
        {{"action": "split", "directions": [<list_of_directions>]}}
        """
        
        self.agent = autogen.AssistantAgent(
            name=f"explorer_{explorer_id}",
            system_message=system_message,
                        code_execution_config={"last_n_messages": 3, "work_dir": "coding", "use_docker": False},

            llm_config=llm_config
        )
        
        self.user_proxy = autogen.UserProxyAgent(
            name=f"user_proxy_{explorer_id}",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
                        code_execution_config={"last_n_messages": 3, "work_dir": "coding", "use_docker": False},

            llm_config=llm_config
        )
        
        self.position = position
        self.id = explorer_id
        self.path = [position]
    
class ExplorerAgent:
    def __init__(self, position: Tuple[int, int], explorer_id: int):
        system_message = f"""You are maze explorer {explorer_id}. You navigate through a maze trying to reach the goal.
        Your decisions should be based on:
        1. Available valid moves
        2. Your current position
        3. The goal position
        4. Your exploration history
        
        Respond with a JSON object containing:
        {{"action": "move", "direction": <chosen_direction>}}
        or
        {{"action": "split", "directions": [<list_of_all_valid_moves>]}}
        """
        
        self.agent = autogen.AssistantAgent(
            name=f"explorer_{explorer_id}",
            system_message=system_message,
                        code_execution_config={"last_n_messages": 3, "work_dir": "coding", "use_docker": False}
,
            llm_config=llm_config
        )
        
        self.user_proxy = autogen.UserProxyAgent(
            name=f"user_proxy_{explorer_id}",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
                        code_execution_config={"last_n_messages": 3, "work_dir": "coding", "use_docker": False}
,
            llm_config=llm_config
        )
        
        self.position = position
        self.id = explorer_id
        self.path = [position]
    
    async def decide_move(self, valid_moves: List[Tuple[int, int]], goal: Tuple[int, int]):
        # Modified to explicitly encourage exploration of multiple paths
        state_message = f"""Current position: {self.position}
        Valid moves: {valid_moves}
        Number of valid moves: {len(valid_moves)}
        Goal position: {goal}
        Path taken: {self.path}
        
        You are at a point in the maze with {len(valid_moves)} possible moves.
        If there are multiple valid moves, you should split to explore all paths.
        
        If multiple moves available:
        Return: {{"action": "split", "directions": <list_of_all_valid_moves>}}
        
        If only one move available:
        Return: {{"action": "move", "direction": <the_valid_move>}}
        
        Respond with a JSON object following these formats."""
        
        chat_response = await self.user_proxy.a_initiate_chat(
            self.agent,
            message=state_message
        )
        
        try:
            last_message = chat_response.last_message()
            if last_message:
                decision = json.loads(last_message.content)
                # If there are multiple moves, force a split action
                if len(valid_moves) > 1:
                    return {"action": "split", "directions": valid_moves}
                return {"action": "move", "direction": valid_moves[0]}
            else:
                return {"action": "move", "direction": valid_moves[0]}
        except (json.JSONDecodeError, AttributeError):
            if len(valid_moves) > 1:
                return {"action": "split", "directions": valid_moves}
            return {"action": "move", "direction": valid_moves[0]}

class MazeCoordinator:
    def __init__(self):
        system_message = """You are a maze exploration coordinator. Your role is to:
        1. Coordinate multiple explorer agents
        2. Track exploration progress
        3. Decide when to create new agents
        4. Determine when the solution is found
        5. Optimize the exploration strategy
        """
        
        self.coordinator = autogen.AssistantAgent(
            name="coordinator",
            system_message=system_message,
                        code_execution_config={"last_n_messages": 3, "work_dir": "coding", "use_docker": False},

            llm_config=llm_config
        )
        
        self.user_proxy = autogen.UserProxyAgent(
            name="coordinator_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
                        code_execution_config={"last_n_messages": 3, "work_dir": "coding", "use_docker": False},

            llm_config=llm_config
        )
        
        # Initialize all required attributes
        self.environment = MazeEnvironment()
        self.explorers = {}
        self.next_explorer_id = 0
        self.solution_found = False
        self.solution_path = None

    def create_explorer(self, position: Tuple[int, int]) -> int:
        explorer_id = self.next_explorer_id
        self.next_explorer_id += 1
        
        explorer = ExplorerAgent(position, explorer_id)
        self.explorers[explorer_id] = explorer
        return explorer_id

    async def coordinate_exploration(self):
        self.create_explorer(START)
        
        while not self.solution_found and self.explorers:
            active_positions = {e.position for e in self.explorers.values()}
            self.environment.visualize(active_positions)
            
            for explorer_id, explorer in list(self.explorers.items()):
                if explorer.position == END:
                    self.solution_found = True
                    self.solution_path = explorer.path
                    print(f"\n🎉 Explorer {explorer_id} found the goal!")
                    return
                
                valid_moves = self.environment.get_valid_moves(explorer.position)
                valid_moves = [m for m in valid_moves if m not in self.environment.visited]
                
                if not valid_moves:
                    print(f"\n💀 Explorer {explorer_id} reached dead end")
                    del self.explorers[explorer_id]
                    continue
                
                decision = await explorer.decide_move(valid_moves, END)
                
                if decision["action"] == "split" and len(valid_moves) > 1:
                    for i, new_pos in enumerate(valid_moves[1:], 1):
                        self.environment.visited.add(new_pos)
                        new_id = self.create_explorer(new_pos)
                        self.explorers[new_id].path = explorer.path + [new_pos]
                        print(f"\n🆕 Created Explorer {new_id} at position {new_pos} (path {i} of {len(valid_moves)})")
                
                next_pos = valid_moves[0]
                self.environment.visited.add(next_pos)
                explorer.position = next_pos
                explorer.path.append(next_pos)
                print(f"\n➡️ Explorer {explorer_id} moved to {next_pos}")
            
            await asyncio.sleep(0.2)
        
        if self.solution_found:
            print("\n✨ Solution found!")
            print("Path:", self.solution_path)
        else:
            print("\n❌ No solution found - all paths explored!")

    async def run(self):
        print("🚀 Starting coordinated maze exploration...")
        await self.coordinate_exploration()

async def main():
    print("🚀 Starting parallel maze exploration with AutoGen agents...")
    coordinator = MazeCoordinator()
    await coordinator.coordinate_exploration()

if __name__ == "__main__":
    asyncio.run(main())