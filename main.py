import autogen
from typing import List, Tuple, Set
import asyncio
import os

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

# Shared state for all agents
shared_state = {
    "visited": set([START]),
    "solution_found": False,
    "solution_path": None,
    "active_agents": set(),
    "total_visited": 0
}

class MazeCoordinator:
    def __init__(self):
        self.coordinator = autogen.AssistantAgent(
            name="coordinator",
            system_message="""You are a maze exploration coordinator. Your role is to:
            1. Track all explorer agents
            2. Create new agents when needed
            3. Monitor exploration progress
            4. Manage the shared state
            5. Determine when the solution is found""",
            llm_config={
                "temperature": 0,
                "request_timeout": 600,
                "seed": 42
            }
        )
        
        self.active_explorers = {}
        self.next_explorer_id = 0

    def get_valid_moves(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        x, y = position
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        valid_moves = []
        
        for dx, dy in directions:
            new_pos = (x + dx, y + dy)
            if (0 <= new_pos[0] < len(MAZE) and 
                0 <= new_pos[1] < len(MAZE[0]) and 
                MAZE[new_pos[0]][new_pos[1]] == 0 and 
                new_pos not in shared_state["visited"]):
                valid_moves.append(new_pos)
        
        return valid_moves

    def create_explorer(self, position: Tuple[int, int], path: List[Tuple[int, int]]):
        explorer_id = self.next_explorer_id
        self.next_explorer_id += 1
        
        explorer = autogen.AssistantAgent(
            name=f"explorer_{explorer_id}",
            system_message=f"""You are maze explorer {explorer_id}. Your current position is {position}.
            Your role is to explore the maze and find paths to the goal.""",
            llm_config={
                "temperature": 0,
                "request_timeout": 600,
                "seed": 42
            }
        )
        
        self.active_explorers[explorer_id] = {
            "agent": explorer,
            "position": position,
            "path": path
        }
        
        shared_state["active_agents"].add(explorer_id)
        return explorer_id

    async def visualize_maze(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
        for i in range(len(MAZE)):
            for j in range(len(MAZE[0])):
                pos = (i, j)
                if pos == START:
                    print("🔵", end=" ")
                elif pos == END:
                    print("🔴", end=" ")
                elif any(e["position"] == pos for e in self.active_explorers.values()):
                    print("🟢", end=" ")
                elif pos in shared_state["visited"]:
                    print("·", end=" ")
                elif MAZE[i][j] == 1:
                    print("█", end=" ")
                else:
                    print(" ", end=" ")
            print()
        
        print("\nLegend: 🔵=Start 🔴=End 🟢=Agent ·=Visited █=Wall")
        print(f"Active Agents: {len(self.active_explorers)}")
        print(f"Total Visited: {len(shared_state['visited'])}")

    async def run_exploration(self):
        # Create initial explorer
        initial_id = self.create_explorer(START, [START])
        
        # Start exploration loop
        while not shared_state["solution_found"] and self.active_explorers:
            # Create tasks for all active explorers
            explorer_tasks = []
            
            for explorer_id, explorer_data in list(self.active_explorers.items()):
                position = explorer_data["position"]
                
                # Check if reached goal
                if position == END:
                    shared_state["solution_found"] = True
                    shared_state["solution_path"] = explorer_data["path"]
                    print(f"\n🎉 Explorer {explorer_id} found the goal!")
                    return
                
                # Get valid moves
                valid_moves = self.get_valid_moves(position)
                
                if not valid_moves:
                    # Remove dead-end explorer
                    print(f"\n💀 Explorer {explorer_id} reached dead end")
                    del self.active_explorers[explorer_id]
                    shared_state["active_agents"].remove(explorer_id)
                    continue
                
                # Spawn new explorers for additional paths
                if len(valid_moves) > 1:
                    for new_pos in valid_moves[1:]:
                        shared_state["visited"].add(new_pos)
                        new_path = explorer_data["path"] + [new_pos]
                        new_id = self.create_explorer(new_pos, new_path)
                        print(f"\n🆕 Created Explorer {new_id} at position {new_pos}")
                
                # Move current explorer
                next_pos = valid_moves[0]
                shared_state["visited"].add(next_pos)
                explorer_data["position"] = next_pos
                explorer_data["path"].append(next_pos)
                print(f"\n➡️ Explorer {explorer_id} moved to {next_pos}")
            
            # Visualize current state
            await self.visualize_maze()
            await asyncio.sleep(0.2)  # Slow down visualization
        
        if shared_state["solution_found"]:
            print("\n✨ Solution found!")
            print("Path:", shared_state["solution_path"])
        else:
            print("\n❌ No solution found - all paths explored!")

async def main():
    print("🚀 Starting parallel maze exploration...")
    coordinator = MazeCoordinator()
    await coordinator.run_exploration()

if __name__ == "__main__":
    asyncio.run(main())