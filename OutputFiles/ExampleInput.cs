using System.Collections.Generic;

namespace Assets.Scripts.DialogueSystem.DialogueSamples
{
	public class ExampleInput : DialogueFile
	{
		public override DialogueLayoutType LayoutType => DialogueLayoutType.Talk;

		public override DialogueTree Dialogue =>
			new(
			);
	}
}
