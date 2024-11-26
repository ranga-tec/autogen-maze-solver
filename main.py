import asyncio
import os
from typing import List, Tuple, Set
import random
from dataclasses import dataclass

# Same maze definition as before...
MAZE = [
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
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

@dataclass
class AgentState:
    position: Tuple[int, int]
    path: List[Tuple[int, int]]

class ParallelMazeSolver:
    def __init__(self):
        self.visited = set([START])
        self.active_agents = {}  # agent_id -> AgentState
        self.visualization_lock = asyncio.Lock()
        self.solution_found = asyncio.Event()
        self.solution_path = None
        self.next_agent_id = 0
        self.active_positions = set([START])
        self.agent_tasks = set()  # Keep track of all agent tasks

    def get_valid_moves(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        x, y = position
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        valid_moves = []
        
        for dx, dy in directions:
            new_pos = (x + dx, y + dy)
            if (0 <= new_pos[0] < len(MAZE) and 
                0 <= new_pos[1] < len(MAZE[0]) and 
                MAZE[new_pos[0]][new_pos[1]] == 0 and 
                new_pos not in self.visited):
                valid_moves.append(new_pos)
        
        return valid_moves

    async def visualize(self):
        while not self.solution_found.is_set() and (self.active_agents or self.agent_tasks):
            async with self.visualization_lock:
                os.system('cls' if os.name == 'nt' else 'clear')
                
                for i in range(len(MAZE)):
                    for j in range(len(MAZE[0])):
                        pos = (i, j)
                        if pos in self.active_positions:
                            print("🟢", end=" ")
                        elif pos == START:
                            print("🔵", end=" ")
                        elif pos == END:
                            print("🔴", end=" ")
                        elif pos in self.visited:
                            print("·", end=" ")
                        elif MAZE[i][j] == 1:
                            print("█", end=" ")
                        else:
                            print(" ", end=" ")
                    print()
                
                print("\nLegend: 🔵=Start 🔴=End 🟢=Agent ·=Visited █=Wall")
                print(f"Active Agents: {len(self.active_agents)}")
                print(f"Running Tasks: {len(self.agent_tasks)}")
                print(f"Total Visited: {len(self.visited)}")
            
            await asyncio.sleep(0.1)

    async def explore(self, agent_id: int, state: AgentState):
        try:
            while not self.solution_found.is_set():
                if state.position == END:
                    print(f"\n🎉 Agent {agent_id} found the solution!")
                    self.solution_path = state.path
                    self.solution_found.set()
                    return

                valid_moves = self.get_valid_moves(state.position)
                
                if not valid_moves:
                    print(f"\n💀 Agent {agent_id} reached dead end")
                    async with self.visualization_lock:
                        self.active_positions.remove(state.position)
                        if agent_id in self.active_agents:
                            del self.active_agents[agent_id]
                    return

                # Spawn new agents for additional paths
                if len(valid_moves) > 1:
                    for new_pos in valid_moves[1:]:
                        self.visited.add(new_pos)
                        new_agent_id = self.next_agent_id
                        self.next_agent_id += 1
                        new_path = state.path + [new_pos]
                        new_state = AgentState(new_pos, new_path)
                        self.active_agents[new_agent_id] = new_state
                        self.active_positions.add(new_pos)
                        task = asyncio.create_task(self.explore(new_agent_id, new_state))
                        self.agent_tasks.add(task)
                        task.add_done_callback(self.agent_tasks.discard)

                # Continue with first path
                next_pos = valid_moves[0]
                self.visited.add(next_pos)
                async with self.visualization_lock:
                    self.active_positions.remove(state.position)
                    self.active_positions.add(next_pos)
                
                state.position = next_pos
                state.path.append(next_pos)
                
                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Error in Agent {agent_id}: {e}")
        finally:
            async with self.visualization_lock:
                if agent_id in self.active_agents:
                    self.active_positions.remove(state.position)
                    del self.active_agents[agent_id]

    async def solve(self):
        # Start initial agent
        initial_state = AgentState(START, [START])
        self.active_agents[0] = initial_state
        
        # Start visualization in parallel
        viz_task = asyncio.create_task(self.visualize())
        
        # Start initial exploration
        initial_task = asyncio.create_task(self.explore(0, initial_state))
        self.agent_tasks.add(initial_task)
        initial_task.add_done_callback(self.agent_tasks.discard)
        
        # Wait for solution or all agents to finish
        while not self.solution_found.is_set() and (self.active_agents or self.agent_tasks):
            await asyncio.sleep(0.1)
        
        # Cancel visualization
        viz_task.cancel()
        try:
            await viz_task
        except asyncio.CancelledError:
            pass

        if self.solution_path:
            print("\nSolution found!")
            print("Path:", self.solution_path)
        else:
            print("\nNo solution found - all paths explored!")

async def main():
    solver = ParallelMazeSolver()
    print("Starting parallel maze exploration...")
    await solver.solve()

if __name__ == "__main__":
    asyncio.run(main())