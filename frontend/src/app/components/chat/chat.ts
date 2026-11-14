import { Component, inject, input, signal } from '@angular/core';
import { APIService, Source } from '../../app.service';


interface Message{
  role : 'user' | 'assistant';
  text : string;
  sources : Source[];
}

@Component({
  imports: [],
  selector: 'app-chat',
  template: `
  <section> 
    <h2> Ask about it</h2>

    @for( m of messages(); track $index){
      <div class="msg" [class.user]="m.role === 'user'">
        <p class="text">{{m.text}}</p>
        @if(m.sources.length){
          <div class="sources">
            Sources : 
            @for (s of m.sources; track s.n) {
              <span [title]="s.preview">[{{s.n}}] page {{s.page}}</span>
            }
          </div>
    }
      </div>
    }
    <div class="ask">
      <input #q placeholder="Ask a question about this document" [disabled]="streaming()" (keydown.enter)="ask(q)" />
      <button [disabled]="streaming()" (click)="ask(q)">Ask</button>
    </div>
  </section>
  `,
})
export class Chat {

  private api = inject(APIService);
  documentId = input.required<string>();
  messages = signal<Message[]>([]);
  streaming = signal(false);

  async ask(box: HTMLInputElement): Promise<void>{
    const question = box.value.trim();
    if(!question || this.streaming())
      return;

    box.value = '';
    this.streaming.set(true);
    this.messages.update((list) => [
      ...list ,
      {role: 'user', text: question, sources: []},
      {role: 'assistant', text: '', sources: []}
    ]);

    await this.api.streamChat(this.documentId(), question, {
      onSources: (sources) => this.updateLast((m) => ({...m,sources})),
      onError: (message) => this.updateLast((m) => ({...m,text:`Error: ${message}`})),
      onToken: (token) => this.updateLast((m) => ({...m, text: m.text + token }))
    });

    this.streaming.set(false);
  }

  private updateLast(change: (m: Message) => Message): void{
    this.messages.update((list) => [...list.slice(0, -1), change(list[list.length - 1])]);
  }


}
