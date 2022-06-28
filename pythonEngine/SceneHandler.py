import basicFunctions
import ObjectPython
from SavingSystemUpgrade import SaveLoadSystem

saveloadmanager = SaveLoadSystem(".save", "save_data_folder")

SceneObjects = saveloadmanager.load_game_data(["Objects"], [[ObjectPython.Object()]])
saveloadmanager.save_game_data([SceneObjects], ["Objects"])
