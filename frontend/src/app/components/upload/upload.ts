import { HttpEventType } from '@angular/common/http';
import { Component, DestroyRef, Inject, inject, output,signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subscription, exhaustMap, takeWhile, timer } from 'rxjs';
import { APIService, DocumentInfo } from '../../app.service';



@Component({
  imports: [],
  selector: 'app-upload',
  template:  `
  <section>
    <h2> Upload a Document (PDF only)</h2>
    <input type="file" accept="application/pdf" [disabled]="busy()" (change)="onFileSelected($event)" />

    @if(uploadPercent() !== null){
      <p> Uploading : {{ uploadPercent() }} %</p>
    }

    @if(doc(); as d){
      <p> 
        <strong>{{ d.filename }}</strong>: {{d.status }}
        @if(d.status ==='processing' && d.total_chunks > 0){
          ({{ d.embedded_chunks }} / {{ d.total_chunks }} chunks embedded)
         }
      </p>
        }

        @if(error()){
          <p class="error">{{ error() }} </p>
        }
  </section>
  `,
})
export class Upload {
  private api = inject(APIService);
  private destroyRef = inject(DestroyRef);
  private subsciption?: Subscription;

  started = output<void>();
  ready = output<DocumentInfo>();

  busy = signal(false);
  uploadPercent = signal<number | null>(null);
  doc = signal<DocumentInfo | null>(null);
  error = signal<string | null>(null);

  onFileSelected(event: Event): void{
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if(!file) return;

    this.subsciption?.unsubscribe();
    this.doc.set(null);
    this.error.set(null);
    this.busy.set(true);
    this.started.emit();

    this.api.upload(file).subscribe({
      next: (e) => {
        if(e.type === HttpEventType.UploadProgress && e.total){
          this.uploadPercent.set(Math.round((100 * e.loaded) / e.total));
        }
        if(e.type === HttpEventType.Response && e.body) {
          this.uploadPercent.set(null);
          this.doc.set(e.body);
          this.pollStatus(e.body.id);
        }
      },
      error: (err) => this.fail(err.error?.detail ?? 'Upload failed. Check backend is running on port 8000.'),
    });
  }

  private pollStatus(id:string): void{
    this.subsciption = timer(0, 1500)
    .pipe(
      exhaustMap(() => this.api.getDocument(id)),
      takeWhile((d) => d.status === 'pending' || d.status === 'processing', true),
      takeUntilDestroyed(this.destroyRef),
    )
    .subscribe({
      next: (d) => {
        this.doc.set(d);
        if(d.status === 'done'){
          this.busy.set(false);
          this.ready.emit(d);
        }
        if(d.status === 'failed') this.fail(d.error ?? 'Processing Failed.');
      },
      error: () => this.fail('Lost contact with the backend while checking status.'),
    });
  }

  private fail(message:string): void {
    this.uploadPercent.set(null);
    this.error.set(message);
    this.busy.set(false);
  }
}
